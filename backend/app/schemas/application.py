"""
Application Pydantic Schemas

Handles job applications with human-in-the-loop controls.
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, validator, field_validator, model_validator
from app.models.application import ApplicationStatus


# ============================================================================
# CREATE SCHEMAS
# ============================================================================

class ApplicationCreate(BaseModel):
    """Schema for creating a new application"""
    job_id: int = Field(..., description="ID of the job being applied to")
    candidate_id: int = Field(..., description="ID of the candidate applying")
    resume_id: Optional[int] = Field(None, description="ID of the resume used for this application")
    cover_letter: Optional[str] = Field(None, max_length=5000, description="Optional cover letter")
    source: Optional[str] = Field(None, description="Application source (e.g., 'linkedin', 'direct', 'referral')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": 1,
                "candidate_id": 42,
                "resume_id": 15,
                "cover_letter": "I am excited to apply for this position...",
                "source": "linkedin"
            }
        }


# ============================================================================
# UPDATE SCHEMAS
# ============================================================================

class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status (pipeline transitions)"""
    status: ApplicationStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Optional notes about the status change")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "screening_passed",
                "notes": "Candidate performed well in AI screening"
            }
        }


class ApplicationReview(BaseModel):
    """
    Schema for HR human review (CRITICAL: human-in-the-loop override)
    This allows HR to override AI recommendations.
    """
    human_decision: str = Field(..., description="HR decision: 'approve', 'reject', or 'pending'")
    human_notes: str = Field(..., min_length=10, description="HR reasoning (required, min 10 chars)")
    rejection_reason: Optional[str] = Field(None, description="Required if human_decision is 'reject'")
    rejection_category: Optional[str] = Field(
        None, 
        description="Category: 'skills', 'experience', 'culture_fit', 'salary', 'location', 'other'"
    )
    
    @validator('human_decision')
    def validate_human_decision(cls, v):
        """Ensure human_decision is valid"""
        if v not in ['approve', 'reject', 'pending']:
            raise ValueError("human_decision must be 'approve', 'reject', or 'pending'")
        return v
    
    @model_validator(mode='after')
    def validate_rejection_fields(self):
        """Ensure rejection_reason is provided when rejecting"""
        if self.human_decision == 'reject' and not self.rejection_reason:
            raise ValueError("rejection_reason is required when human_decision is 'reject'")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "human_decision": "approve",
                "human_notes": "Strong technical skills and great culture fit. Recommended for interview.",
                "rejection_reason": None,
                "rejection_category": None
            }
        }


class ApplicationUpdate(BaseModel):
    """General application update schema"""
    status: Optional[ApplicationStatus] = None
    cover_letter: Optional[str] = None
    human_decision: Optional[str] = None
    human_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    rejection_category: Optional[str] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ApplicationResponse(BaseModel):
    """Full application response with all fields"""
    # Primary fields
    id: int
    job_id: int
    candidate_id: int
    resume_id: Optional[int]
    status: ApplicationStatus
    cover_letter: Optional[str]
    source: Optional[str]
    
    # AI Matching Scores
    resume_match_score: Optional[float] = Field(None, description="Resume match score (0-100)")
    skills_match_score: Optional[float] = Field(None, description="Skills match score (0-100)")
    experience_match_score: Optional[float] = Field(None, description="Experience match score (0-100)")
    overall_match_score: Optional[float] = Field(None, description="Overall match score (0-100)")
    
    # AI Recommendations
    ai_recommendation: Optional[str] = Field(None, description="AI recommendation: strong_fit/good_fit/weak_fit/no_fit")
    ai_recommendation_reason: Optional[str] = Field(None, description="AI explanation for recommendation")
    match_highlights: Optional[List[str]] = Field(None, description="Key strengths identified by AI")
    match_gaps: Optional[List[str]] = Field(None, description="Key gaps identified by AI")
    
    # Pipeline Integration
    screening_score: Optional[float] = Field(None, description="Score from AI screening (0-100)")
    screening_passed: Optional[bool] = Field(None, description="Whether candidate passed screening")
    interview_score: Optional[float] = Field(None, description="Score from interview (0-100)")
    interview_completed: Optional[bool] = Field(None, description="Whether interview is completed")
    
    # Human Review (CRITICAL: Human-in-the-loop)
    human_decision: Optional[str] = Field(None, description="HR decision: approve/reject/pending")
    human_notes: Optional[str] = Field(None, description="HR notes and reasoning")
    reviewed_by: Optional[int] = Field(None, description="User ID of reviewer")
    reviewed_at: Optional[datetime] = Field(None, description="Timestamp of review")
    
    # Rejection Tracking
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    rejection_category: Optional[str] = None
    
    # Timestamps
    applied_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "job_id": 5,
                "candidate_id": 42,
                "resume_id": 15,
                "status": "screening_passed",
                "cover_letter": "I am excited to apply...",
                "source": "linkedin",
                "resume_match_score": 87.5,
                "skills_match_score": 92.0,
                "experience_match_score": 78.5,
                "overall_match_score": 86.0,
                "ai_recommendation": "strong_fit",
                "ai_recommendation_reason": "Candidate has 5+ years Python experience and FastAPI expertise...",
                "match_highlights": ["5 years Python", "FastAPI expert", "PostgreSQL experience"],
                "match_gaps": ["No AWS experience", "Limited React knowledge"],
                "screening_score": 85.0,
                "screening_passed": True,
                "interview_score": None,
                "interview_completed": False,
                "human_decision": "approve",
                "human_notes": "Strong technical skills, recommended for interview",
                "reviewed_by": 1,
                "reviewed_at": "2025-11-06T16:30:00",
                "rejected_at": None,
                "rejection_reason": None,
                "rejection_category": None,
                "applied_at": "2025-11-05T10:00:00",
                "updated_at": "2025-11-06T16:30:00"
            }
        }


class ApplicationListResponse(BaseModel):
    """Paginated list of applications"""
    total: int = Field(..., description="Total number of applications")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    applications: List[ApplicationResponse] = Field(..., description="List of applications")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "page": 1,
                "page_size": 20,
                "applications": []
            }
        }


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class PipelineAnalytics(BaseModel):
    """Pipeline analytics and metrics"""
    total_applications: int = Field(..., description="Total number of applications")
    
    # By Status
    by_status: Dict[str, int] = Field(..., description="Count of applications by status")
    
    # Conversion Rates
    screening_conversion_rate: float = Field(..., description="% of applied → screening_passed")
    interview_conversion_rate: float = Field(..., description="% of screening_passed → interview_completed")
    offer_conversion_rate: float = Field(..., description="% of interview_completed → offer_extended")
    
    # Time Metrics
    avg_time_to_screen: Optional[float] = Field(None, description="Average days from applied to screening_passed")
    avg_time_to_interview: Optional[float] = Field(None, description="Average days from screening_passed to interview_completed")
    avg_time_to_hire: Optional[float] = Field(None, description="Average days from applied to offer_accepted")
    
    # AI Performance
    ai_recommendation_distribution: Dict[str, int] = Field(
        ..., 
        description="Count by AI recommendation (strong_fit, good_fit, weak_fit, no_fit)"
    )
    human_override_rate: float = Field(
        ..., 
        description="% of times HR decision differs from AI recommendation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_applications": 150,
                "by_status": {
                    "applied": 45,
                    "screening": 30,
                    "screening_passed": 25,
                    "interview_scheduled": 15,
                    "interview_completed": 12,
                    "shortlisted": 8,
                    "offer_extended": 5,
                    "offer_accepted": 3,
                    "rejected": 7
                },
                "screening_conversion_rate": 55.6,
                "interview_conversion_rate": 48.0,
                "offer_conversion_rate": 41.7,
                "avg_time_to_screen": 2.5,
                "avg_time_to_interview": 5.3,
                "avg_time_to_hire": 14.2,
                "ai_recommendation_distribution": {
                    "strong_fit": 40,
                    "good_fit": 65,
                    "weak_fit": 35,
                    "no_fit": 10
                },
                "human_override_rate": 12.5
            }
        }
