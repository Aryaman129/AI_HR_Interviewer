"""
Job-related Pydantic schemas for API validation
Based on database models and API requirements
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    DIRECTOR = "director"

class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=5000)
    requirements: Optional[str] = Field(None, max_length=3000)
    location: Optional[str] = Field(None, max_length=100)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    employment_type: EmploymentType = Field(default=EmploymentType.FULL_TIME)
    remote_option: bool = Field(default=False)
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.MID)
    skills_required: Optional[List[str]] = Field(default=None)
    department: Optional[str] = Field(None, max_length=100)
    
    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than or equal to salary_min')
        return v
    
    @validator('skills_required')
    def validate_skills(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError('Maximum 20 skills allowed')
            for skill in v:
                if len(skill.strip()) == 0:
                    raise ValueError('Skills cannot be empty')
        return v

class JobCreate(JobBase):
    """Schema for creating a new job"""
    pass

class JobUpdate(BaseModel):
    """Schema for updating an existing job"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    requirements: Optional[str] = Field(None, max_length=3000)
    location: Optional[str] = Field(None, max_length=100)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    employment_type: Optional[EmploymentType] = None
    remote_option: Optional[bool] = None
    experience_level: Optional[ExperienceLevel] = None
    skills_required: Optional[List[str]] = None
    department: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    
    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than or equal to salary_min')
        return v

class JobResponse(BaseModel):
    """Schema for job responses - maps from Job model"""
    id: int
    title: str
    company: str  # Maps from company_name in model
    description: str
    requirements: Optional[str] = None  # Will be converted from list to string
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment_type: str  # Maps from job_type in model
    remote_option: bool  # Maps from is_remote in model
    experience_level: str
    skills_required: Optional[List[str]] = None  # Maps from required_skills in model
    department: Optional[str] = None
    is_active: bool  # Maps from status field (active/inactive)
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_orm(cls, db_job):
        """Custom ORM converter to handle field name mismatches"""
        return cls(
            id=db_job.id,
            title=db_job.title,
            company=db_job.company_name,  # company_name → company
            description=db_job.description,
            requirements=' '.join(db_job.requirements) if db_job.requirements else None,  # list → string
            location=db_job.location,
            salary_min=db_job.salary_min,
            salary_max=db_job.salary_max,
            employment_type=db_job.job_type.value if hasattr(db_job.job_type, 'value') else str(db_job.job_type),  # job_type → employment_type
            remote_option=db_job.is_remote,  # is_remote → remote_option
            experience_level=db_job.experience_level.value if hasattr(db_job.experience_level, 'value') else str(db_job.experience_level),
            skills_required=db_job.required_skills,  # required_skills → skills_required
            department=db_job.department,
            is_active=(db_job.status == "active" or str(db_job.status).lower() == "active"),  # status → is_active
            organization_id=db_job.organization_id,
            created_at=db_job.created_at,
            updated_at=db_job.updated_at
        )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class JobSearchResponse(BaseModel):
    """Schema for job search results"""
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class JobMatchResult(BaseModel):
    """Schema for job-candidate match results"""
    job_id: int
    candidate_id: int
    overall_score: float = Field(..., ge=0.0, le=1.0)
    component_scores: Dict[str, float]
    job_requirements: Dict[str, Any]
    match_explanation: str
    created_at: datetime

class CandidateMatchResponse(BaseModel):
    """Schema for candidate match response"""
    candidate_id: int
    candidate_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    component_scores: Dict[str, float]
    explanation: str

class JobAnalytics(BaseModel):
    """Schema for job analytics response"""
    job_id: int
    total_candidates_in_system: int
    candidates_analyzed: int
    match_score_distribution: Dict[str, int]
    average_match_score: float
    top_matching_skills: List[str]
    recommendations: List[str]