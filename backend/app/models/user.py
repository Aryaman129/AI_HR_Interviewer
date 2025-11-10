"""
User Model
HR users, hiring managers, and administrators
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    """User roles and permissions"""
    ADMIN = "admin"  # Full system access
    HR_MANAGER = "hr_manager"  # Manage jobs, candidates, make hiring decisions
    RECRUITER = "recruiter"  # View candidates, schedule interviews
    HIRING_MANAGER = "hiring_manager"  # Review candidates for specific jobs
    VIEWER = "viewer"  # Read-only access


class User(Base):
    """Platform users (HR team, hiring managers)"""
    __tablename__ = "users"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    department = Column(String(100))
    job_title = Column(String(100))
    
    # Role & Permissions
    role = Column(SQLEnum(UserRole), default=UserRole.RECRUITER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime)
    
    # Organization (Multi-tenancy)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    # Legacy fields (deprecated in favor of organization relationship)
    company_name = Column(String(255))
    company_size = Column(String(50))  # "1-10", "11-50", "51-200", etc.
    industry = Column(String(100))
    
    # Settings
    preferences = Column(JSONB)  # User preferences and settings
    # Example: {
    #   "notifications": {"email": true, "sms": false},
    #   "timezone": "Asia/Kolkata",
    #   "language": "en"
    # }
    
    # Security
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(50))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)  # Account lockout
    password_changed_at = Column(DateTime)
    
    # API Access
    api_key = Column(String(255), unique=True)  # For API integrations
    api_key_created_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)  # Soft delete
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    jobs_created = relationship("Job", foreign_keys="Job.created_by", back_populates="created_by_user")
    jobs_managed = relationship("Job", foreign_keys="Job.hiring_manager_id", back_populates="hiring_manager")
    feedbacks_given = relationship("Feedback", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.full_name} ({self.email})>"
    
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role == UserRole.ADMIN
    
    @property
    def can_manage_jobs(self) -> bool:
        """Check if user can create/edit jobs"""
        return self.role in [UserRole.ADMIN, UserRole.HR_MANAGER, UserRole.HIRING_MANAGER]
