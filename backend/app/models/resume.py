"""
Resume Model
Stores parsed resume data and AI-extracted information
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Resume(Base):
    """Resume/CV model with AI-extracted structured data"""
    __tablename__ = "resumes"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    
    # File Information
    filename = Column(String(255), nullable=False)
    file_url = Column(Text)  # S3/R2 storage URL
    file_size_bytes = Column(Integer)
    file_type = Column(String(10))  # pdf, docx, txt
    
    # Extracted Content
    raw_text = Column(Text)  # Full text extracted from PDF/DOCX
    cleaned_text = Column(Text)  # Preprocessed text for AI analysis
    
    # AI-Parsed Information (via spaCy + Custom NER)
    parsed_data = Column(JSONB)  # Complete parsed resume structure
    # Example structure:
    # {
    #   "contact": {"email": "...", "phone": "...", "location": "..."},
    #   "summary": "Experienced software engineer...",
    #   "skills": {
    #     "technical": ["Python", "FastAPI", "PostgreSQL"],
    #     "soft": ["Leadership", "Communication"],
    #     "tools": ["Docker", "Git", "VS Code"]
    #   },
    #   "experience": [
    #     {
    #       "company": "Acme Corp",
    #       "role": "Senior SDE",
    #       "duration": "2020-2023",
    #       "responsibilities": ["Led API team", "Migrated to microservices"],
    #       "achievements": ["Reduced latency by 40%"]
    #     }
    #   ],
    #   "education": [
    #     {
    #       "degree": "B.Tech Computer Science",
    #       "institution": "IIT Delhi",
    #       "year": "2018",
    #       "grade": "8.5 CGPA"
    #     }
    #   ],
    #   "certifications": ["AWS Solutions Architect", "Kubernetes CKA"],
    #   "projects": [{"name": "...", "description": "...", "tech": [...]}],
    #   "languages": ["English", "Hindi", "Tamil"]
    # }
    
    # AI Quality Metrics
    parsing_confidence = Column(Float)  # 0.0 to 1.0 confidence score
    completeness_score = Column(Float)  # How complete is the resume (0-100)
    formatting_quality = Column(Float)  # How well-formatted (0-100)
    
    # Skills Analysis
    technical_skills_count = Column(Integer)
    total_experience_months = Column(Integer)  # Calculated from experience section
    education_level = Column(String(50))  # "bachelors", "masters", "phd", "diploma"
    
    # NLP/AI Processing
    entities_extracted = Column(JSONB)  # All named entities found by spaCy
    keywords = Column(JSONB)  # Important keywords extracted
    
    # Validation & Flags
    is_valid = Column(Boolean, default=True)  # Is resume parseable and valid?
    validation_errors = Column(JSONB)  # List of validation issues
    has_contact_info = Column(Boolean, default=False)
    has_work_experience = Column(Boolean, default=False)
    has_education = Column(Boolean, default=False)
    
    # Processing Status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text)  # Error message if parsing failed
    processed_at = Column(DateTime)
    
    # Versioning (if candidate uploads multiple resumes)
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True)
    superseded_by = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")
    superseded_resume = relationship("Resume", remote_side=[id], uselist=False)
    
    def __repr__(self):
        return f"<Resume {self.filename} for Candidate {self.candidate_id}>"
    
    @property
    def file_extension(self) -> str:
        """Get file extension"""
        return self.file_type or self.filename.split(".")[-1] if self.filename else ""
    
    @property
    def is_processed(self) -> bool:
        """Check if resume has been successfully processed"""
        return self.processing_status == "completed" and self.is_valid
