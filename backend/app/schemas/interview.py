"""
Interview Pydantic Schemas (Pydantic v2)

Handles voice/video interviews with AI analysis and session control.
Mirrors Application API pattern (42/42 tests passing).
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.interview import InterviewStatus, SessionState


# ============================================================================
# CREATE SCHEMAS
# ============================================================================

class InterviewCreate(BaseModel):
    """Schema for creating/scheduling a new interview"""
    candidate_id: int = Field(..., description="ID of the candidate being interviewed")
    job_id: int = Field(..., description="ID of the job position")
    application_id: Optional[int] = Field(None, description="ID of the related application")
    
    # Multi-tenant fields (CRITICAL for staffing agencies)
    organization_id: Optional[int] = Field(None, description="Organization ID (for multi-tenant support)")
    client_id: Optional[int] = Field(None, description="Client ID (for staffing agencies managing multiple clients)")
    
    # Interview configuration
    interview_type: str = Field(..., description="Type: 'voice', 'video', or 'phone'")
    platform: str = Field(default="twilio", description="Platform: 'twilio', 'zoom', 'teams', 'manual'")
    duration_minutes: int = Field(default=30, ge=5, le=180, description="Planned duration (5-180 minutes)")
    scheduled_at: datetime = Field(..., description="Scheduled start time (ISO 8601)")
    
    # Optional metadata
    phone_number_used: Optional[str] = Field(None, max_length=20, description="Phone number for voice interviews")
    
    @field_validator('interview_type')
    @classmethod
    def validate_interview_type(cls, v: str) -> str:
        """Ensure interview_type is valid"""
        allowed = ['voice', 'video', 'phone']
        if v not in allowed:
            raise ValueError(f"interview_type must be one of: {allowed}")
        return v
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Ensure platform is valid"""
        allowed = ['twilio', 'zoom', 'teams', 'manual']
        if v not in allowed:
            raise ValueError(f"platform must be one of: {allowed}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": 42,
                "job_id": 5,
                "application_id": 12,
                "organization_id": 1,
                "client_id": 3,
                "interview_type": "voice",
                "platform": "twilio",
                "duration_minutes": 30,
                "scheduled_at": "2025-11-10T14:00:00Z",
                "phone_number_used": "+1-555-0123"
            }
        }


# ============================================================================
# SESSION CONTROL SCHEMAS
# ============================================================================

class InterviewSessionControl(BaseModel):
    """
    Schema for session control actions (pause/resume/complete/abandon)
    CRITICAL: Real-time session management during live interviews
    """
    action: str = Field(..., description="Action: 'start', 'pause', 'resume', 'complete', or 'abandon'")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes about the action", validation_alias="reason")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Ensure action is valid"""
        allowed = ['start', 'pause', 'resume', 'complete', 'abandon']
        if v not in allowed:
            raise ValueError(f"action must be one of: {allowed}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "pause",
                "notes": "Candidate requested 5-minute break"
            }
        }


# ============================================================================
# UPDATE SCHEMAS
# ============================================================================

class InterviewStatusUpdate(BaseModel):
    """Schema for updating interview status"""
    status: InterviewStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes about the status change")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "notes": "Interview completed successfully"
            }
        }


class InterviewFeedback(BaseModel):
    """
    Schema for human interviewer feedback (CRITICAL: Human-in-the-loop)
    This allows interviewers to add notes and ratings post-interview.
    
    Note: interviewer_id is NOT in the request - it's set from the authenticated user.
    """
    interviewer_notes: str = Field(..., min_length=10, description="Detailed feedback (required, min 10 chars)")
    interviewer_rating: int = Field(..., ge=1, le=10, description="Rating from 1-10")
    
    # Optional override fields
    technical_score: Optional[float] = Field(None, ge=0, le=100, description="Override AI technical score (0-100)")
    communication_score: Optional[float] = Field(None, ge=0, le=100, description="Override AI communication score (0-100)")
    enthusiasm_score: Optional[float] = Field(None, ge=0, le=100, description="Override AI enthusiasm score (0-100)")
    culture_fit_score: Optional[float] = Field(None, ge=0, le=100, description="Override AI culture fit score (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "interviewer_notes": "Candidate demonstrated strong technical skills and excellent communication. Highly recommend for next round.",
                "interviewer_rating": 9,
                "technical_score": 92.0,
                "communication_score": 88.0,
                "enthusiasm_score": 85.0,
                "culture_fit_score": 90.0
            }
        }


class InterviewUpdate(BaseModel):
    """General interview update schema (partial updates)"""
    status: Optional[InterviewStatus] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=180)
    
    # Recording & transcription
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    transcript_confidence: Optional[float] = Field(None, ge=0, le=1)
    
    # Human interviewer notes
    interviewer_notes: Optional[str] = Field(None, description="Human interviewer notes and observations")
    
    # AI analysis
    ai_analysis: Optional[Dict[str, Any]] = None
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    technical_score: Optional[float] = Field(None, ge=0, le=100)
    communication_score: Optional[float] = Field(None, ge=0, le=100)
    enthusiasm_score: Optional[float] = Field(None, ge=0, le=100)
    culture_fit_score: Optional[float] = Field(None, ge=0, le=100)
    
    ai_recommendation: Optional[str] = None
    ai_summary: Optional[str] = None
    key_strengths: Optional[List[str]] = None
    key_concerns: Optional[List[str]] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class InterviewResponse(BaseModel):
    """Full interview response with all fields"""
    # Primary fields
    id: int
    candidate_id: int
    job_id: Optional[int]
    application_id: Optional[int]
    
    # Multi-tenant fields
    organization_id: Optional[int] = Field(None, description="Organization ID for multi-tenant support")
    client_id: Optional[int] = Field(None, description="Client ID for staffing agencies")
    
    # Interview configuration
    interview_type: str = Field(..., description="Type: voice/video/phone")
    platform: str = Field(..., description="Platform used")
    duration_minutes: int = Field(..., description="Planned duration")
    
    # Scheduling
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled start time")
    started_at: Optional[datetime] = Field(None, description="Actual start time")
    ended_at: Optional[datetime] = Field(None, description="Actual end time")
    actual_duration_seconds: Optional[int] = Field(None, description="Actual duration in seconds")
    
    # Status & Session State
    status: str = Field(..., description="Status: scheduled/in_progress/completed/cancelled/no_show")
    session_state: str = Field(..., description="Session state: scheduled/in_progress/paused/completed/abandoned")
    
    # Session tracking (NEW)
    paused_at: Optional[datetime] = Field(None, description="When session was paused")
    resumed_at: Optional[datetime] = Field(None, description="When session was resumed")
    last_activity_at: Optional[datetime] = Field(None, description="Last user interaction")
    pause_count: int = Field(default=0, description="Number of times paused")
    
    # Recording & Transcription
    recording_url: Optional[str] = Field(None, description="Audio/video recording URL")
    recording_sid: Optional[str] = Field(None, description="Twilio recording SID")
    transcript: Optional[str] = Field(None, description="Full transcription")
    transcript_confidence: Optional[float] = Field(None, description="Whisper confidence score (0-1)")
    
    # Questions & Responses
    questions: Optional[Dict[str, Any]] = Field(None, description="Questions asked during interview")
    responses: Optional[Dict[str, Any]] = Field(None, description="Candidate responses (segmented)")
    
    # AI Analysis
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed AI evaluation")
    overall_score: Optional[float] = Field(None, description="Overall score (0-100)")
    technical_score: Optional[float] = Field(None, description="Technical score (0-100)")
    communication_score: Optional[float] = Field(None, description="Communication score (0-100)")
    enthusiasm_score: Optional[float] = Field(None, description="Enthusiasm score (0-100)")
    culture_fit_score: Optional[float] = Field(None, description="Culture fit score (0-100)")
    
    # AI Recommendations
    ai_recommendation: Optional[str] = Field(None, description="AI recommendation: strong_hire/hire/maybe/no_hire")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    key_strengths: Optional[List[str]] = Field(None, description="Key strengths identified")
    key_concerns: Optional[List[str]] = Field(None, description="Key concerns identified")
    
    # Human Feedback (CRITICAL: Human-in-the-loop)
    interviewer_id: Optional[int] = Field(None, description="ID of human interviewer")
    interviewer_notes: Optional[str] = Field(None, description="Human interviewer notes")
    interviewer_rating: Optional[int] = Field(None, description="Human rating (1-10)")
    
    # Technical Metadata
    call_sid: Optional[str] = Field(None, description="Twilio call SID")
    phone_number_used: Optional[str] = Field(None, description="Phone number used")
    ip_address: Optional[str] = Field(None, description="Candidate IP address")
    user_agent: Optional[str] = Field(None, description="Candidate user agent")
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "candidate_id": 42,
                "job_id": 5,
                "application_id": 12,
                "organization_id": 1,
                "client_id": 3,
                "interview_type": "voice",
                "platform": "twilio",
                "duration_minutes": 30,
                "scheduled_at": "2025-11-10T14:00:00Z",
                "started_at": "2025-11-10T14:02:15Z",
                "ended_at": "2025-11-10T14:28:45Z",
                "actual_duration_seconds": 1590,
                "status": "completed",
                "session_state": "completed",
                "paused_at": None,
                "resumed_at": None,
                "last_activity_at": "2025-11-10T14:28:45Z",
                "pause_count": 0,
                "recording_url": "https://cdn.example.com/interviews/1.mp3",
                "recording_sid": "RE1234567890abcdef",
                "transcript": "Full interview transcript here...",
                "transcript_confidence": 0.94,
                "questions": {"q1": "Tell me about your experience with Python"},
                "responses": {"r1": "I have 5 years of Python experience..."},
                "ai_analysis": {"communication_score": 8, "technical_knowledge": 7},
                "overall_score": 85.5,
                "technical_score": 82.0,
                "communication_score": 88.0,
                "enthusiasm_score": 86.0,
                "culture_fit_score": 85.0,
                "ai_recommendation": "strong_hire",
                "ai_summary": "Candidate demonstrated strong technical skills...",
                "key_strengths": ["Strong Python knowledge", "Excellent communication"],
                "key_concerns": ["Limited cloud experience"],
                "interviewer_id": 5,
                "interviewer_notes": "Very impressed with candidate",
                "interviewer_rating": 9,
                "call_sid": "CA1234567890abcdef",
                "phone_number_used": "+1-555-0123",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "created_at": "2025-11-08T10:00:00Z",
                "updated_at": "2025-11-10T14:30:00Z"
            }
        }


class InterviewListResponse(BaseModel):
    """Paginated list of interviews"""
    total: int = Field(..., description="Total number of interviews")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    interviews: List[InterviewResponse] = Field(..., description="List of interviews")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 75,
                "page": 1,
                "page_size": 20,
                "interviews": []
            }
        }


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class InterviewAnalytics(BaseModel):
    """Interview analytics and metrics"""
    total_interviews: int = Field(..., description="Total number of interviews")
    
    # By Status
    by_status: Dict[str, int] = Field(..., description="Count of interviews by status")
    
    # By Session State
    by_session_state: Dict[str, int] = Field(..., description="Count by session state")
    
    # By Interview Type
    by_type: Dict[str, int] = Field(..., description="Count by interview type (voice/video/phone)")
    
    # By Platform
    by_platform: Dict[str, int] = Field(..., description="Count by platform (twilio/zoom/teams)")
    
    # Completion Metrics
    completion_rate: float = Field(..., description="% of scheduled interviews that were completed")
    no_show_rate: float = Field(..., description="% of scheduled interviews with no-shows")
    cancellation_rate: float = Field(..., description="% of scheduled interviews that were cancelled")
    
    # Session Metrics (NEW)
    avg_pause_count: float = Field(..., description="Average number of pauses per interview")
    sessions_with_pauses: int = Field(..., description="Number of sessions that had at least one pause")
    pause_rate: float = Field(..., description="% of sessions that were paused")
    
    # Duration Metrics
    avg_duration_minutes: Optional[float] = Field(None, description="Average actual duration in minutes")
    median_duration_minutes: Optional[float] = Field(None, description="Median actual duration")
    
    # Score Metrics
    avg_overall_score: Optional[float] = Field(None, description="Average overall score (0-100)")
    avg_technical_score: Optional[float] = Field(None, description="Average technical score")
    avg_communication_score: Optional[float] = Field(None, description="Average communication score")
    avg_enthusiasm_score: Optional[float] = Field(None, description="Average enthusiasm score")
    avg_culture_fit_score: Optional[float] = Field(None, description="Average culture fit score")
    
    # AI Recommendations
    ai_recommendation_distribution: Dict[str, int] = Field(
        ..., 
        description="Count by AI recommendation (strong_hire/hire/maybe/no_hire)"
    )
    
    # Human Feedback Metrics
    avg_interviewer_rating: Optional[float] = Field(None, description="Average human interviewer rating (1-10)")
    interviews_with_feedback: int = Field(..., description="Number of interviews with human feedback")
    feedback_rate: float = Field(..., description="% of completed interviews with human feedback")
    
    # Multi-tenant Metrics (NEW)
    by_organization: Optional[Dict[str, int]] = Field(None, description="Count by organization (if multi-tenant)")
    by_client: Optional[Dict[str, int]] = Field(None, description="Count by client (for staffing agencies)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_interviews": 75,
                "by_status": {
                    "scheduled": 15,
                    "in_progress": 5,
                    "completed": 45,
                    "cancelled": 7,
                    "no_show": 3
                },
                "by_session_state": {
                    "scheduled": 15,
                    "in_progress": 5,
                    "completed": 45,
                    "paused": 2,
                    "abandoned": 8
                },
                "by_type": {
                    "voice": 40,
                    "video": 25,
                    "phone": 10
                },
                "by_platform": {
                    "twilio": 50,
                    "zoom": 15,
                    "teams": 10
                },
                "completion_rate": 75.0,
                "no_show_rate": 5.0,
                "cancellation_rate": 11.7,
                "avg_pause_count": 0.6,
                "sessions_with_pauses": 12,
                "pause_rate": 26.7,
                "avg_duration_minutes": 28.5,
                "median_duration_minutes": 27.0,
                "avg_overall_score": 78.5,
                "avg_technical_score": 76.0,
                "avg_communication_score": 82.0,
                "avg_enthusiasm_score": 79.5,
                "avg_culture_fit_score": 77.0,
                "ai_recommendation_distribution": {
                    "strong_hire": 15,
                    "hire": 20,
                    "maybe": 8,
                    "no_hire": 2
                },
                "avg_interviewer_rating": 7.8,
                "interviews_with_feedback": 38,
                "feedback_rate": 84.4,
                "by_organization": {"org_1": 50, "org_2": 25},
                "by_client": {"client_1": 30, "client_2": 20, "client_3": 25}
            }
        }
