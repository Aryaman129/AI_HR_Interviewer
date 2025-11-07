"""
Interview Model  
Voice/Video interview records with AI analysis
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from app.db.database import Base


class InterviewStatus(str, Enum):
    """Interview status enumeration"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class SessionState(str, Enum):
    """Interview session state enumeration"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Interview(Base):
    """Voice/Video interview session with AI transcription and evaluation"""
    __tablename__ = "interviews"
    
    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    
    # Multi-Tenant Support (CRITICAL for staffing agencies)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    client_id = Column(Integer, nullable=True, index=True)  # For staffing agencies managing multiple clients
    
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
    
    # Session State Tracking (NEW - mirrors Screening model)
    session_state = Column(String(50), default="scheduled")  # scheduled, in_progress, paused, completed, abandoned
    paused_at = Column(DateTime)  # When session was paused
    resumed_at = Column(DateTime)  # When session was resumed
    last_activity_at = Column(DateTime)  # Last user interaction timestamp
    pause_count = Column(Integer, default=0)  # Track how many times paused
    
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
    organization = relationship("Organization", foreign_keys=[organization_id])
    
    def __repr__(self):
        return f"<Interview {self.id} ({self.interview_type}) for Candidate {self.candidate_id}>"
    
    @property
    def was_completed(self) -> bool:
        """Check if interview was successfully completed"""
        return self.status == "completed" and self.transcript is not None
    
    # Session Management Methods (NEW - mirrors Screening model)
    def pause_session(self) -> None:
        """Pause the interview session"""
        if self.session_state != SessionState.IN_PROGRESS.value:
            raise ValueError(f"Cannot pause interview in state: {self.session_state}")
        
        self.session_state = SessionState.PAUSED.value
        self.paused_at = datetime.utcnow()
        self.pause_count = (self.pause_count or 0) + 1
        
    def resume_session(self) -> None:
        """Resume the paused interview session"""
        if self.session_state != SessionState.PAUSED.value:
            raise ValueError(f"Cannot resume interview in state: {self.session_state}")
        
        now = datetime.utcnow()
        self.session_state = SessionState.IN_PROGRESS.value
        self.resumed_at = now
        self.last_activity_at = now
        
    def complete_session(self) -> None:
        """Mark the interview session as completed"""
        now = datetime.utcnow()
        self.session_state = SessionState.COMPLETED.value
        self.status = InterviewStatus.COMPLETED.value
        self.ended_at = now
        
        # Calculate actual duration
        if self.started_at:
            self.actual_duration_seconds = int((now - self.started_at).total_seconds())
        
    def start_session(self) -> None:
        """Start the interview session"""
        if self.session_state != SessionState.SCHEDULED.value:
            raise ValueError(f"Cannot start interview in state: {self.session_state}")
        
        now = datetime.utcnow()
        self.session_state = SessionState.IN_PROGRESS.value
        self.status = InterviewStatus.IN_PROGRESS.value
        self.started_at = now
        self.last_activity_at = now
    
    def abandon_session(self) -> None:
        """Mark the session as abandoned (candidate left without completing)"""
        self.session_state = SessionState.ABANDONED.value
        self.status = InterviewStatus.NO_SHOW.value
        self.last_activity_at = datetime.utcnow()
