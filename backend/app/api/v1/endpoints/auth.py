"""
Authentication Endpoints
Handles user registration, login, token refresh, and password management
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    UserInfo,
    RefreshTokenRequest,
    RefreshTokenResponse,
    PasswordChangeRequest,
    MessageResponse
)
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.dependencies.auth import get_current_user

router = APIRouter()


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters with uppercase, lowercase, and digit
    - **full_name**: User's full name
    - **organization_id**: Optional organization ID (required for non-admin users)
    - **role**: User role (default: RECRUITER)
    
    Returns JWT access token and user information.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verify organization exists if provided
    if user_data.organization_id:
        organization = db.query(Organization).filter(
            Organization.id == user_data.organization_id
        ).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
    
    # Check if this is the first user (auto-admin)
    user_count = db.query(User).count()
    if user_count == 0:
        # First user becomes admin
        role = UserRole.ADMIN
        organization_id = None  # Admin can access all organizations
    else:
        # Subsequent users need organization_id
        if not user_data.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id is required for non-admin users"
            )
        role = user_data.role or UserRole.RECRUITER
        organization_id = user_data.organization_id
    
    # Create new user
    try:
        new_user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=role,
            organization_id=organization_id,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Generate JWT tokens
    access_token = create_access_token(
        data={"sub": new_user.id, "org_id": new_user.organization_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": new_user.id}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo.model_validate(new_user)
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    - **email**: User email address
    - **password**: User password
    
    Returns JWT access token, refresh token, and user information.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked due to too many failed login attempts. Try again later."
        )
    
    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        
        # Lock account if too many failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts. Try again in 30 minutes."
            )
        
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Reset failed login attempts and update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Generate JWT tokens
    access_token = create_access_token(
        data={"sub": user.id, "org_id": user.organization_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo.model_validate(user)
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new access token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode refresh token
        payload = decode_token(token_data.refresh_token)
        
        # Verify token type
        if not verify_token_type(payload, "refresh"):
            raise credentials_exception
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None or not user.is_active:
        raise credentials_exception
    
    # Generate new access token
    access_token = create_access_token(
        data={"sub": user.id, "org_id": user.organization_id}
    )
    
    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserInfo.model_validate(current_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for current authenticated user.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters with uppercase, lowercase, and digit)
    
    Requires valid JWT token in Authorization header.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Check if new password is different from current
    if verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return MessageResponse(message="Password changed successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    Note: Since we're using stateless JWT, this is mainly for client-side token removal.
    For a complete logout, implement token blacklisting or use shorter token expiration.
    
    Requires valid JWT token in Authorization header.
    """
    # In a production system, you might:
    # 1. Add the token to a blacklist/cache (Redis)
    # 2. Store token JTI in database for revocation checking
    # 3. Update user's last_logout_at timestamp
    
    return MessageResponse(message="Logged out successfully. Please remove the token from client.")
