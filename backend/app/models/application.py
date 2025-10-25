"""
Application Model
Links candidates to job postings and tracks application status
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class ApplicationStatus(str, enum.Enum):
    """Application pipeline status"""
    APPLIED = "applied"
    SCREENING = "screening"
    SCREENING_PASSED = "screening_passed"
    SCREENING_FAILED = "screening_failed"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    SHORTLISTED = "shortlisted"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base):
    """Job application linking candidate to job posting"""
    __tablename__ = "applications"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    
    # Application Details
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.APPLIED, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))  # Which resume was used
    cover_letter = Column(Text)  # Optional cover letter
    
    # Source & Metadata
    source = Column(String(100))  # "naukri", "linkedin", "direct", "referral"
    referrer_email = Column(String(255))  # If referred by someone
    utm_source = Column(String(100))  # Marketing attribution
    
    # AI Matching Scores (0-100)
    resume_match_score = Column(Float)  # How well resume matches job requirements
    skills_match_score = Column(Float)  # Skills overlap percentage
    experience_match_score = Column(Float)  # Experience level match
    overall_match_score = Column(Float)  # Weighted composite score
    
    # AI Recommendations
    ai_recommendation = Column(String(50))  # "strong_fit", "good_fit", "weak_fit", "no_fit"
    ai_recommendation_reason = Column(Text)  # Explanation of AI decision
    match_highlights = Column(JSONB)  # ["5 years Python exp", "FastAPI expert"]
    match_gaps = Column(JSONB)  # ["No AWS experience", "Lacks React skills"]
    
    # Screening Results
    screening_id = Column(Integer, ForeignKey("screenings.id"))
    screening_score = Column(Float)  # 0-100 from AI screening
    screening_passed = Column(Integer)  # Boolean as integer
    
    # Interview Results
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    interview_score = Column(Float)  # 0-100 from voice/video interview
    interview_completed = Column(Integer)  # Boolean
    
    # Human Review
    reviewed_by = Column(Integer, ForeignKey("users.id"))  # HR who reviewed
    reviewed_at = Column(DateTime)
    human_decision = Column(String(50))  # "approve", "reject", "pending"
    human_notes = Column(Text)  # HR comments
    
    # Rejection Info
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)
    rejection_category = Column(String(100))  # "skills_mismatch", "experience", "culture_fit"
    
    # Timestamps
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime)
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    resume = relationship("Resume")
    screening = relationship("Screening", back_populates="application", uselist=False)
    interview = relationship("Interview", back_populates="application", uselist=False)
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<Application {self.id}: Candidate {self.candidate_id} -> Job {self.job_id}>"
    
    @property
    def is_active(self) -> bool:
        """Check if application is still in progress"""
        return self.status not in [
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.OFFER_REJECTED,
            ApplicationStatus.OFFER_ACCEPTED
        ]
    
    @property
    def is_successful(self) -> bool:
        """Check if application led to hire"""
        return self.status == ApplicationStatus.OFFER_ACCEPTED
