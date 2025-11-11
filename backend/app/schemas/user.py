"""
User Schemas for API Request/Response
Handles user CRUD operations with validation
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a new user (admin only)"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: str  # Will validate against UserRole enum
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        """
        Validate password strength - must handle special characters!
        Required: min 8 chars, 1 uppercase, 1 lowercase, 1 digit
        Special characters allowed (bcrypt handles them fine)
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        """
        Validate role against UserRole enum
        Prevents Phase 1 bug (invalid "interviewer" role)
        """
        valid_roles = [role.value for role in UserRole]
        if v not in valid_roles:
            raise ValueError(
                f'Invalid role: {v}. Must be one of: {", ".join(valid_roles)}'
            )
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@testorg.com",
                "password": "SecurePass123!@#",
                "full_name": "John Doe",
                "role": "recruiter",
                "phone": "+1-555-0123",
                "department": "Human Resources",
                "job_title": "Senior Recruiter"
            }
        }


class UserUpdate(BaseModel):
    """
    Schema for updating a user
    
    Security Notes:
    - Email changes NOT allowed (high-security operation, deferred to Phase 5)
    - Password changes require current password (handled in endpoint)
    - Role changes require admin privileges (enforced in endpoint)
    """
    # email: Optional[EmailStr] = None  # REMOVED - security requirement
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = None  # Admin-only (enforced in endpoint)
    
    @validator('password')
    def password_strength(cls, v):
        """Same validation as UserCreate"""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        """Validate role if provided"""
        if v is None:
            return v
        valid_roles = [role.value for role in UserRole]
        if v not in valid_roles:
            raise ValueError(
                f'Invalid role: {v}. Must be one of: {", ".join(valid_roles)}'
            )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe Updated",
                "phone": "+1-555-9999",
                "department": "Talent Acquisition",
                "job_title": "Lead Recruiter"
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user data in responses (excludes hashed_password)"""
    id: int
    email: EmailStr
    full_name: str
    role: str
    phone: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    organization_id: int
    is_active: bool
    is_verified: bool
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None  # For soft delete visibility
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 3,
                "email": "john.doe@testorg.com",
                "full_name": "John Doe",
                "role": "recruiter",
                "phone": "+1-555-0123",
                "department": "Human Resources",
                "job_title": "Senior Recruiter",
                "organization_id": 1,
                "is_active": True,
                "is_verified": True,
                "email_verified_at": "2025-11-11T10:00:00",
                "last_login_at": "2025-11-11T15:30:00",
                "created_at": "2025-11-01T09:00:00",
                "updated_at": "2025-11-11T15:30:00",
                "deleted_at": None
            }
        }
    )


class UserListResponse(BaseModel):
    """Schema for paginated user list"""
    items: list[UserResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "email": "hr@testorg.com",
                        "full_name": "HR Manager",
                        "role": "hr_manager",
                        "organization_id": 1,
                        "is_active": True,
                        "is_verified": True,
                        "created_at": "2025-11-01T09:00:00",
                        "updated_at": "2025-11-01T09:00:00",
                        "deleted_at": None
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        }
