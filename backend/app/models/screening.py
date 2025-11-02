"""
Screening Model
AI-based candidate screening with questions and evaluations
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from app.db.database import Base


class ScreeningStatus(str, Enum):
    """Screening status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SessionState(str, Enum):
    """Interview session state enumeration"""
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


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
    
    # Session State Tracking (NEW)
    session_state = Column(String(50), default="in_progress")  # in_progress, paused, completed, abandoned
    paused_at = Column(DateTime)  # When session was paused
    resumed_at = Column(DateTime)  # When session was resumed
    last_activity_at = Column(DateTime)  # Last user interaction timestamp
    
    # Session Metadata (NEW) - Transcript, Recording, Key Points
    session_metadata = Column(JSONB)
    # Example: {
    #   "pause_count": 2,
    #   "total_paused_seconds": 300,
    #   "time_per_question": [45, 120, 89],  # seconds per question
    #   "recording_url": "https://storage/interview_123.mp4",  # optional
    #   "transcript": [  # conversation transcript
    #     {"speaker": "ai", "text": "Tell me about your Python experience", "timestamp": "00:00:05"},
    #     {"speaker": "candidate", "text": "I have 5 years experience...", "timestamp": "00:00:10"}
    #   ],
    #   "key_points_discussed": [  # extracted key topics
    #     "Python experience - 5 years",
    #     "FastAPI - built 3 production APIs",
    #     "Database - PostgreSQL, MongoDB"
    #   ],
    #   "ai_observations": [  # real-time AI notes
    #     "Candidate showed strong technical depth",
    #     "Communication style: clear and concise"
    #   ]
    # }
    
    # Scoring Breakdown (NEW) - Detailed score justification
    scoring_breakdown = Column(JSONB)
    # Example: {
    #   "question_scores": [
    #     {
    #       "question_id": 1,
    #       "score": 8,
    #       "max_score": 10,
    #       "reason": "Demonstrated strong understanding of async/await",
    #       "criteria_met": ["depth", "clarity", "examples"],
    #       "criteria_missed": ["edge_cases"]
    #     }
    #   ],
    #   "category_scores": {
    #     "technical_skills": 85,
    #     "problem_solving": 75,
    #     "communication": 90,
    #     "cultural_fit": 80
    #   },
    #   "scoring_rationale": "Strong technical candidate with excellent communication"
    # }
    
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
    
    # Session Management Methods
    def pause_session(self) -> None:
        """Pause the interview session"""
        self.session_state = SessionState.PAUSED.value
        self.paused_at = datetime.utcnow()
        
        # Update pause count in metadata
        if not self.session_metadata:
            self.session_metadata = {}
        
        pause_count = self.session_metadata.get('pause_count', 0)
        self.session_metadata['pause_count'] = pause_count + 1
        
    def resume_session(self) -> None:
        """Resume the paused interview session"""
        now = datetime.utcnow()
        
        # Calculate paused duration
        if self.paused_at:
            paused_seconds = (now - self.paused_at).total_seconds()
            
            if not self.session_metadata:
                self.session_metadata = {}
            
            total_paused = self.session_metadata.get('total_paused_seconds', 0)
            self.session_metadata['total_paused_seconds'] = total_paused + paused_seconds
        
        self.session_state = SessionState.IN_PROGRESS.value
        self.resumed_at = now
        self.last_activity_at = now
        
    def complete_session(self) -> None:
        """Mark the interview session as completed"""
        now = datetime.utcnow()
        self.session_state = SessionState.COMPLETED.value
        self.completed_at = now
        self.is_completed = 1
        
        # Calculate total time excluding pauses
        if self.started_at:
            total_elapsed = (now - self.started_at).total_seconds()
            paused_seconds = 0
            
            if self.session_metadata:
                paused_seconds = self.session_metadata.get('total_paused_seconds', 0)
            
            self.total_time_seconds = int(total_elapsed - paused_seconds)
            
    def abandon_session(self) -> None:
        """Mark the session as abandoned (candidate left without completing)"""
        self.session_state = SessionState.ABANDONED.value
        self.last_activity_at = datetime.utcnow()
        
    def add_transcript_entry(self, speaker: str, text: str, timestamp: str = None) -> None:
        """Add an entry to the interview transcript"""
        if not self.session_metadata:
            self.session_metadata = {}
        
        if 'transcript' not in self.session_metadata:
            self.session_metadata['transcript'] = []
        
        if not timestamp:
            # Calculate time from start
            if self.started_at:
                elapsed = (datetime.utcnow() - self.started_at).total_seconds()
                mins, secs = divmod(int(elapsed), 60)
                timestamp = f"{mins:02d}:{secs:02d}"
            else:
                timestamp = "00:00"
        
        self.session_metadata['transcript'].append({
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp
        })
        
    def add_key_point(self, key_point: str) -> None:
        """Add a key point discussed during the interview"""
        if not self.session_metadata:
            self.session_metadata = {}
        
        if 'key_points_discussed' not in self.session_metadata:
            self.session_metadata['key_points_discussed'] = []
        
        self.session_metadata['key_points_discussed'].append(key_point)
        
    def add_ai_observation(self, observation: str) -> None:
        """Add an AI observation about the candidate"""
        if not self.session_metadata:
            self.session_metadata = {}
        
        if 'ai_observations' not in self.session_metadata:
            self.session_metadata['ai_observations'] = []
        
        self.session_metadata['ai_observations'].append(observation)
