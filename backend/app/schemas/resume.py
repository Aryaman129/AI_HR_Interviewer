"""
Pydantic schemas for parsed resumes

These models represent the structured JSON we expect from the LLM resume parser
and are used to validate/shape the parser output before storing it in the DB.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None


class WorkExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class SkillsModel(BaseModel):
    technical: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: SkillsModel = Field(default_factory=SkillsModel)
    education: List[EducationItem] = Field(default_factory=list)
    work_experience: List[WorkExperienceItem] = Field(default_factory=list)
    total_experience_years: Optional[float] = None
    raw_text: Optional[str] = None
    parsed_at: Optional[datetime] = None
    # Optional embeddings (added by parser implementation)
    resume_embedding: Optional[List[float]] = None
    skills_embedding: Optional[List[float]] = None

    class Config:
        # Allow populating from ORM objects if needed and encode datetimes
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
