"""
Screening Model
AI-based candidate screening with questions and evaluations
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Screening(Base):
    """AI screening assessment with questions and responses"""
    __tablename__ = "screenings"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True)
    
    # Screening Configuration
    screening_type = Column(String(50), default="ai_generated")  # ai_generated, template, custom
    total_questions = Column(Integer)
    
    # Questions & Responses
    questions = Column(JSONB)  # List of screening questions
    # Example: [
    #   {
    #     "id": 1,
    #     "question": "Explain your experience with FastAPI",
    #     "type": "technical",  # technical, behavioral, situational
    #     "difficulty": "medium",
    #     "category": "backend_development"
    #   }
    # ]
    
    responses = Column(JSONB)  # Candidate's answers
    # Example: [
    #   {
    #     "question_id": 1,
    #     "answer": "I have 3 years experience with FastAPI...",
    #     "answered_at": "2025-10-25T10:30:00Z",
    #     "time_taken_seconds": 120
    #   }
    # ]
    
    # AI Evaluation
    ai_evaluation = Column(JSONB)  # Detailed AI scoring per question
    # Example: [
    #   {
    #     "question_id": 1,
    #     "score": 8,  # 1-10
    #     "evaluation": "Strong understanding of FastAPI concepts",
    #     "key_points": ["Mentioned dependency injection", "Async/await"],
    #     "missing_points": ["No mention of OpenAPI docs"]
    #   }
    # ]
    
    # Overall Scores
    overall_score = Column(Float)  # 0-100 composite score
    technical_score = Column(Float)  # 0-100
    communication_score = Column(Float)  # 0-100 based on answer quality
    completeness_score = Column(Float)  # How many questions answered
    
    # AI Recommendation
    ai_recommendation = Column(String(50))  # "strong_pass", "pass", "borderline", "fail"
    ai_summary = Column(Text)  # AI-generated summary of screening
    strengths = Column(JSONB)  # ["Strong Python skills", "Good problem-solving"]
    weaknesses = Column(JSONB)  # ["Limited AWS experience", "Weak on system design"]
    
    # Timing & Completion
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    total_time_seconds = Column(Integer)
    is_completed = Column(Integer, default=0)  # Boolean as integer
    questions_answered = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default="pending")  # pending, in_progress, completed, expired
    expiry_date = Column(DateTime)  # When screening link expires
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="screenings")
    job = relationship("Job")
    application = relationship("Application", back_populates="screening")
    
    def __repr__(self):
        return f"<Screening {self.id} for Candidate {self.candidate_id}>"
    
    @property
    def pass_threshold(self) -> float:
        """Minimum score to pass (configurable)"""
        return 60.0
    
    @property
    def did_pass(self) -> bool:
        """Check if candidate passed screening"""
        return self.overall_score >= self.pass_threshold if self.overall_score else False
    
    @property
    def completion_percentage(self) -> float:
        """Percentage of questions answered"""
        if self.total_questions and self.questions_answered:
            return (self.questions_answered / self.total_questions) * 100
        return 0.0
