"""
Interview Model  
Voice/Video interview records with AI analysis
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Interview(Base):
    """Voice/Video interview session with AI transcription and evaluation"""
    __tablename__ = "interviews"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    
    # Interview Type & Configuration
    interview_type = Column(String(50))  # "voice", "video", "phone"
    platform = Column(String(50))  # "twilio", "zoom", "teams", "manual"
    duration_minutes = Column(Integer, default=30)
    
    # Scheduling
    scheduled_at = Column(DateTime, index=True)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    actual_duration_seconds = Column(Integer)
    
    # Status
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed, cancelled, no_show
    
    # Recording & Transcription
    recording_url = Column(Text)  # S3/R2 URL for audio/video file
    recording_sid = Column(String(255))  # Twilio recording SID
    transcript = Column(Text)  # Full transcription via Whisper
    transcript_confidence = Column(Float)  # Whisper confidence score
    
    # Questions & Answers
    questions = Column(JSONB)  # Questions asked during interview
    responses = Column(JSONB)  # Candidate responses (segmented)
    
    # AI Analysis (via Ollama + Llama 3.1)
    ai_analysis = Column(JSONB)  # Detailed AI evaluation
    # Example: {
    #   "communication_score": 8,
    #   "technical_knowledge": 7,
    #   "problem_solving": 9,
    #   "clarity": 8,
    #   "confidence": 7,
    #   "key_insights": ["Strong algorithms knowledge", "Hesitant on system design"]
    # }
    
    # Scores
    overall_score = Column(Float)  # 0-100
    technical_score = Column(Float)
    communication_score = Column(Float)
    enthusiasm_score = Column(Float)
    culture_fit_score = Column(Float)
    
    # AI Recommendations
    ai_recommendation = Column(String(50))  # "strong_hire", "hire", "maybe", "no_hire"
    ai_summary = Column(Text)  # AI-generated interview summary
    key_strengths = Column(JSONB)
    key_concerns = Column(JSONB)
    
    # Interviewer Notes (Human)
    interviewer_id = Column(Integer, ForeignKey("users.id"))
    interviewer_notes = Column(Text)
    interviewer_rating = Column(Integer)  # 1-10
    
    # Technical Metadata
    call_sid = Column(String(255))  # Twilio call SID
    phone_number_used = Column(String(20))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="interviews")
    job = relationship("Job")
    application = relationship("Application", back_populates="interview")
    interviewer = relationship("User", foreign_keys=[interviewer_id])
    
    def __repr__(self):
        return f"<Interview {self.id} ({self.interview_type}) for Candidate {self.candidate_id}>"
    
    @property
    def was_completed(self) -> bool:
        """Check if interview was successfully completed"""
        return self.status == "completed" and self.transcript is not None
