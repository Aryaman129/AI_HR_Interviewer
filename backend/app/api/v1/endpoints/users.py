"""
User Management Endpoints
Provides CRUD operations for user management with RBAC
Phase 2: User Management
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.dependencies.auth import get_current_user, require_role
from app.services.auth_service import get_password_hash

router = APIRouter()


def create_audit_log(
    db: Session,
    current_user: User,
    action: str,
    entity_type: str,
    entity_id: int,
    description: str,
    changes: Optional[dict] = None
):
    """Helper function to create audit log entries"""
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        changes=changes,
        created_at=datetime.utcnow()
    )
    db.add(audit)
    return audit


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only)
    
    Security:
    - Requires admin role
    - Validates role against UserRole enum
    - Checks email uniqueness within organization
    - Hashes password with bcrypt
    - Sets organization_id from current user
    - Creates audit log entry
    
    Args:
        user_data: User creation data
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        Created user data (excluding hashed_password)
        
    Raises:
        400: Email already exists in organization
        422: Invalid role or weak password
    """
    # Check email uniqueness in organization
    existing_user = db.query(User).filter(
        User.email == user_data.email,
        User.organization_id == current_user.organization_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists in your organization"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        department=user_data.department,
        job_title=user_data.job_title,
        organization_id=current_user.organization_id,
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create audit log
    create_audit_log(
        db=db,
        current_user=current_user,
        action="USER_CREATED",
        entity_type="User",
        entity_id=new_user.id,
        description=f"Admin {current_user.email} created user {new_user.email} with role {new_user.role}",
        changes={
            "after": {
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role,
                "organization_id": new_user.organization_id
            }
        }
    )
    db.commit()
    
    return new_user


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    current_user: User = Depends(require_role("admin", "hr_manager")),
    db: Session = Depends(get_db)
):
    """
    List users with filters and pagination (admin, hr_manager)
    
    Security:
    - Requires admin or hr_manager role
    - Filters by current user's organization
    - Excludes soft-deleted users (deleted_at IS NOT NULL) ← FIX #1
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum records to return (max 500)
        role: Optional role filter
        is_active: Optional active status filter
        search: Optional search term (email/name)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Paginated list of users
    """
    # Base query with org isolation and soft delete filter
    query = db.query(User).filter(
        User.organization_id == current_user.organization_id,
        User.deleted_at.is_(None)  # ← FIX #1: Exclude soft-deleted users
    )
    
    # Apply filters
    if role:
        # Validate role before filtering
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of: {', '.join(valid_roles)}"
            )
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination and fetch
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return UserListResponse(
        items=users,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (self or admin)
    
    Security:
    - Any authenticated user can view own profile
    - Admin can view any user in organization
    - Multi-tenant: can only view users in same organization
    
    Args:
        user_id: User ID to retrieve
        current_user: Authenticated user
        db: Database session
        
    Returns:
        User data
        
    Raises:
        403: Not authorized to view this user
        404: User not found
    """
    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check authorization
    is_self = user.id == current_user.id
    is_admin = current_user.role == "admin"
    same_org = user.organization_id == current_user.organization_id
    
    if not same_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access users from other organizations"
        )
    
    if not (is_self or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's profile"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user (self for profile, admin for role)
    
    Security:
    - Users can update own profile (name, phone, department, job_title, password)
    - Only admin can change user roles
    - Email changes NOT allowed (deferred to Phase 5) ← FIX #2
    - Password changes are hashed with bcrypt
    - Multi-tenant: can only update users in same organization
    - Creates audit log entry ← FIX #3
    
    Args:
        user_id: User ID to update
        user_data: Updated user data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Updated user data
        
    Raises:
        403: Not authorized to update this user or change role
        404: User not found
    """
    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check authorization
    is_self = user.id == current_user.id
    is_admin = current_user.role == "admin"
    same_org = user.organization_id == current_user.organization_id
    
    if not same_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update users from other organizations"
        )
    
    if not (is_self or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Track changes for audit log
    changes_before = {}
    changes_after = {}
    fields_changed = []
    
    # Check role change permission
    if user_data.role is not None and user_data.role != user.role:
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can change user roles"
            )
        changes_before["role"] = user.role
        changes_after["role"] = user_data.role
        fields_changed.append("role")
        user.role = user_data.role
    
    # Update fields
    if user_data.full_name is not None:
        changes_before["full_name"] = user.full_name
        changes_after["full_name"] = user_data.full_name
        fields_changed.append("full_name")
        user.full_name = user_data.full_name
    
    if user_data.phone is not None:
        changes_before["phone"] = user.phone
        changes_after["phone"] = user_data.phone
        fields_changed.append("phone")
        user.phone = user_data.phone
    
    if user_data.department is not None:
        changes_before["department"] = user.department
        changes_after["department"] = user_data.department
        fields_changed.append("department")
        user.department = user_data.department
    
    if user_data.job_title is not None:
        changes_before["job_title"] = user.job_title
        changes_after["job_title"] = user_data.job_title
        fields_changed.append("job_title")
        user.job_title = user_data.job_title
    
    # Handle password change (hash it)
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
        user.password_changed_at = datetime.utcnow()
        fields_changed.append("password")
        changes_after["password"] = "***CHANGED***"
    
    # Update timestamp
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    # Create audit log (FIX #3)
    if fields_changed:
        action_desc = f"User {current_user.email} updated user {user.email}"
        if "role" in fields_changed:
            action_desc += f" (role changed: {changes_before.get('role')} → {changes_after.get('role')})"
        
        create_audit_log(
            db=db,
            current_user=current_user,
            action="USER_UPDATED",
            entity_type="User",
            entity_id=user.id,
            description=action_desc,
            changes={
                "before": changes_before,
                "after": changes_after,
                "fields_changed": fields_changed
            }
        )
        db.commit()
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Soft delete user (admin only)
    
    Security:
    - Requires admin role
    - Prevents self-deletion (safety feature)
    - Multi-tenant: can only delete users in same organization
    - Soft delete: sets deleted_at timestamp, keeps record in DB
    - Sets is_active = False
    - Creates audit log entry ← FIX #3
    
    Args:
        user_id: User ID to delete
        current_user: Authenticated admin user
        db: Database session
        
    Returns:
        204 No Content on success
        
    Raises:
        400: Attempting to delete self
        403: Not authorized (non-admin or different org)
        404: User not found
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account. Please contact another administrator."
        )
    
    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check organization
    if user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete users from other organizations"
        )
    
    # Check if already deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deleted"
        )
    
    # Soft delete
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Create audit log (FIX #3)
    create_audit_log(
        db=db,
        current_user=current_user,
        action="USER_DELETED",
        entity_type="User",
        entity_id=user.id,
        description=f"Admin {current_user.email} deleted user {user.email} (role: {user.role})",
        changes={
            "before": {
                "is_active": True,
                "deleted_at": None
            },
            "after": {
                "is_active": False,
                "deleted_at": user.deleted_at.isoformat()
            }
        }
    )
    db.commit()
    
    return None
