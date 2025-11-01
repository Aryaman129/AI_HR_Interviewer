"""
Pydantic schemas for structured resume parsing output.

These models are used to validate the JSON returned by the LLM-based parser
so the rest of the codebase can rely on a stable shape.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class EducationItem(BaseModel):
    degree: Optional[str] = None
    university: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    details: Optional[str] = None


class WorkExperienceItem(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class SkillSet(BaseModel):
    technical: List[str] = Field(default_factory=list)
    soft: List[str] = Field(default_factory=list)


class ResumeParseResult(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    location: Optional[str] = None

    skills: SkillSet = Field(default_factory=SkillSet)
    education: List[EducationItem] = Field(default_factory=list)
    work_experience: List[WorkExperienceItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    # Embeddings (optional - if missing we'll compute them)
    resume_embedding: Optional[List[float]] = None
    skills_embedding: Optional[List[float]] = None

    # Full extracted text and metadata
    raw_text: Optional[str] = None
    parsed_at: Optional[str] = None
    total_experience_years: Optional[float] = None

    class Config:
        extra = "allow"
