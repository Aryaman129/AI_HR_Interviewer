"""Company Knowledge model for RAG system."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.database import Base


class CompanyKnowledge(Base):
    """
    Company knowledge documents for RAG-enhanced AI screening.
    
    Stores company-specific information with vector embeddings for similarity search:
    - Company values and culture
    - Technical requirements and stack
    - Interview styles and preferences
    - Role-specific context
    """
    __tablename__ = "company_knowledge"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False, index=True)  # company_values, tech_requirements, interview_style
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)  # JobBERT-v3 embeddings
    doc_metadata = Column('metadata', JSONB, default={}, server_default='{}')  # Extensible metadata (attribute name to avoid SQLAlchemy reserved 'metadata')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="company_knowledge")
    
    def __repr__(self):
        return f"<CompanyKnowledge(id={self.id}, org={self.organization_id}, type={self.doc_type}, title='{self.title[:30]}')>"
