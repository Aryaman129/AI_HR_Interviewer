"""
Feedback Model
HR feedback and notes on candidates
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class FeedbackType(str, enum.Enum):
    """Type of feedback"""
    RESUME_REVIEW = "resume_review"
    SCREENING_REVIEW = "screening_review"
    INTERVIEW_FEEDBACK = "interview_feedback"
    GENERAL_NOTE = "general_note"
    FINAL_DECISION = "final_decision"


class FeedbackRating(str, enum.Enum):
    """Overall candidate rating"""
    STRONG_YES = "strong_yes"
    YES = "yes"
    MAYBE = "maybe"
    NO = "no"
    STRONG_NO = "strong_no"


class Feedback(Base):
    """HR/Hiring Manager feedback on candidates"""
    __tablename__ = "feedbacks"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    
    # Reviewer
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_role = Column(String(50))  # "hr_manager", "hiring_manager", "team_lead"
    
    # Feedback Details
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    rating = Column(SQLEnum(FeedbackRating))
    score = Column(Integer)  # 1-10 numeric score
    
    # Content
    comments = Column(Text, nullable=False)  # Main feedback text
    strengths = Column(Text)  # What impressed the reviewer
    concerns = Column(Text)  # What are the concerns
    questions_for_next_round = Column(Text)  # Questions for next interview
    
    # Decision
    recommendation = Column(String(50))  # "proceed", "reject", "needs_more_info"
    is_final_decision = Column(Integer, default=0)  # Boolean as integer
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="feedbacks")
    job = relationship("Job")
    application = relationship("Application")
    reviewer = relationship("User", back_populates="feedbacks_given")
    
    def __repr__(self):
        return f"<Feedback {self.id} by User {self.reviewer_id} for Candidate {self.candidate_id}>"
