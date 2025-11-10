"""
Authentication Dependencies
Provides dependency injection for authentication and authorization
"""
from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import decode_token

# OAuth2 scheme - points to login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
        
    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise credentials_exception
        
        # Convert user_id from string to integer
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Check if account is locked
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked due to too many failed login attempts"
        )
    
    return user


async def get_optional_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User | None:
    """
    Dependency to get the current user if token is provided, None otherwise.
    Useful for endpoints that can work both authenticated and unauthenticated.
    
    Args:
        token: Optional JWT token
        db: Database session
        
    Returns:
        User object if token is valid, None otherwise
    """
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory for role-based access control.
    
    Args:
        *allowed_roles: Variable number of UserRole enum values
        
    Returns:
        Dependency function that checks user role
        
    Raises:
        HTTPException: 403 if user doesn't have required role
        
    Usage:
        @router.post("/admin-only")
        async def admin_route(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_role(UserRole.ADMIN))
        ):
            return {"message": "Admin access granted"}
            
        @router.post("/hr-or-manager")
        async def hr_route(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_role(UserRole.HR_MANAGER, UserRole.ADMIN))
        ):
            return {"message": "HR access granted"}
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> None:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}"
            )
    
    return role_checker


async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is an active admin.
    Convenience function for common use case.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if user is admin
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_active_hr_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is an HR manager or admin.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if user is HR manager or admin
        
    Raises:
        HTTPException: 403 if user doesn't have HR manager or admin role
    """
    if current_user.role not in [UserRole.HR_MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR Manager or Admin access required"
        )
    return current_user


def verify_organization_access(
    resource_org_id: int,
    current_user: User
) -> None:
    """
    Verify that the current user has access to a resource from their organization.
    Admins can access all organizations.
    
    Args:
        resource_org_id: Organization ID of the resource
        current_user: Current authenticated user
        
    Raises:
        HTTPException: 403 if user doesn't have access to the organization
        
    Usage:
        @router.get("/jobs/{job_id}")
        async def get_job(
            job_id: int,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise HTTPException(404, "Job not found")
            
            # Check organization access
            verify_organization_access(job.organization_id, current_user)
            
            return job
    """
    # Admins can access all organizations
    if current_user.role == UserRole.ADMIN:
        return
    
    # Check if user belongs to the same organization
    if current_user.organization_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You don't have permission to access this resource."
        )
