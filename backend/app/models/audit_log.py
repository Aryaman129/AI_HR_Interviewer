"""
Audit Log Model
Track all system actions for compliance and debugging
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class AuditLog(Base):
    """System audit trail for compliance and security"""
    __tablename__ = "audit_logs"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    
    # Who
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Null for system actions
    user_email = Column(String(255))  # Cached for reference
    user_role = Column(String(50))
    
    # What
    action = Column(String(100), nullable=False, index=True)  # "candidate_created", "job_updated", etc.
    entity_type = Column(String(50), index=True)  # "candidate", "job", "application", etc.
    entity_id = Column(Integer, index=True)  # ID of affected entity
    
    # Details
    description = Column(Text)  # Human-readable description
    changes = Column(JSONB)  # Before/after values
    # Example: {
    #   "before": {"status": "screening"},
    #   "after": {"status": "shortlisted"},
    #   "fields_changed": ["status"]
    # }
    
    extra_metadata = Column(JSONB)  # Additional context (renamed from 'metadata' to avoid SQLAlchemy conflict)
    # Example: {
    #   "ip_address": "192.168.1.1",
    #   "user_agent": "Mozilla/5.0...",
    #   "api_endpoint": "/api/v1/candidates/123",
    #   "request_id": "abc-123"
    # }
    
    # When & Where
    ip_address = Column(String(50))
    user_agent = Column(Text)
    request_method = Column(String(10))  # GET, POST, PUT, DELETE
    request_path = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type} by User {self.user_id}>"
    
    @classmethod
    def log_action(cls, session, user_id: int, action: str, entity_type: str, entity_id: int, 
                   description: str = None, changes: dict = None, extra_metadata: dict = None):
        """Convenience method to create audit log entry"""
        log = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            changes=changes,
            extra_metadata=extra_metadata
        )
        session.add(log)
        return log
