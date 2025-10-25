"""
Candidate Model
Stores candidate information with resume embeddings for semantic search
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
import enum

from app.db.database import Base


class CandidateStatus(str, enum.Enum):
    """Candidate application status"""
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"
    WITHDRAWN = "withdrawn"


class Candidate(Base):
    """Candidate/Applicant model with vector embeddings for semantic matching"""
    __tablename__ = "candidates"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), index=True)
    full_name = Column(String(255), nullable=False)
    
    # Status & Metadata
    status = Column(SQLEnum(CandidateStatus), default=CandidateStatus.NEW, index=True)
    source = Column(String(100))  # naukri, linkedin, referral, etc.
    location = Column(String(255))
    current_company = Column(String(255))
    current_role = Column(String(255))
    total_experience_years = Column(Integer)  # Total years of experience
    
    # Resume & Profile
    resume_url = Column(Text)  # S3/R2 URL for original resume file
    resume_text = Column(Text)  # Extracted text from resume
    linkedin_url = Column(String(500))
    portfolio_url = Column(String(500))
    
    # AI/ML - Vector Embeddings (384 dimensions for all-MiniLM-L6-v2)
    resume_embedding = Column(Vector(384))  # pgvector column for semantic search
    skills_embedding = Column(Vector(384))  # Separate embedding for skills
    
    # Extracted Information (from AI resume parser)
    skills = Column(JSONB)  # {"technical": [...], "soft": [...]}
    education = Column(JSONB)  # [{"degree": "B.Tech", "institution": "IIT Delhi", ...}]
    work_experience = Column(JSONB)  # [{"company": "Acme", "role": "SDE", "duration": "2 years"}]
    certifications = Column(JSONB)  # [{"name": "AWS SAA", "issued": "2023"}]
    languages = Column(JSONB)  # ["English", "Hindi"]
    
    # Screening Scores
    ai_resume_score = Column(Integer)  # 1-100 score from resume analysis
    ai_screening_score = Column(Integer)  # 1-100 from AI screening questions
    voice_interview_score = Column(Integer)  # 1-100 from voice interview
    overall_score = Column(Integer)  # Weighted average
    
    # Privacy & Consent
    gdpr_consent = Column(Boolean, default=False)
    data_retention_until = Column(DateTime)  # Auto-delete candidate data after this date
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime)
    
    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    screenings = relationship("Screening", back_populates="candidate", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="candidate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Candidate {self.full_name} ({self.email})>"
    
    @property
    def display_name(self) -> str:
        """Human-readable display name"""
        return self.full_name or self.email.split("@")[0]
    
    @property
    def is_active(self) -> bool:
        """Check if candidate is still in active pipeline"""
        return self.status not in [CandidateStatus.REJECTED, CandidateStatus.WITHDRAWN, CandidateStatus.HIRED]
