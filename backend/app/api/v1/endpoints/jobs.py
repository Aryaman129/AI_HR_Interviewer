"""
Job Management API Endpoints
Based on research from open-source AI HR systems
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_

from app.db.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobSearchResponse
from app.services.job_matcher import job_matcher_service
from app.services.resume_parser import get_resume_parser
from app.dependencies.auth import get_current_user, get_current_active_user, require_role

import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Jobs"])

@router.post("/", response_model=JobResponse)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"]))
):
    """
    Create a new job posting with automatic vector embedding generation
    Requires: hr_manager or admin role
    """
    try:
        # Parse requirements string into list if provided
        requirements_list = []
        if job_data.requirements:
            # Split by newlines or periods to create list
            requirements_list = [req.strip() for req in job_data.requirements.replace('\n', '.').split('.') if req.strip()]
        
        # Create job record - Map schema fields to model fields
        db_job = Job(
            title=job_data.title,
            company_name=job_data.company,  # Schema: company → Model: company_name
            description=job_data.description,
            requirements=requirements_list,  # Schema: str → Model: JSONB array
            location=job_data.location,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            job_type=job_data.employment_type.value if hasattr(job_data.employment_type, 'value') else job_data.employment_type,  # Schema: employment_type → Model: job_type
            is_remote=job_data.remote_option,  # Schema: remote_option → Model: is_remote
            experience_level=job_data.experience_level.value if hasattr(job_data.experience_level, 'value') else job_data.experience_level,
            required_skills=job_data.skills_required,  # Schema: skills_required → Model: required_skills
            department=job_data.department,
            status="active",  # Set status to active by default
            organization_id=current_user.organization_id  # Organization isolation
        )
        
        # Generate embeddings for semantic search
        parser = get_resume_parser()
        
        # Create combined text for embedding
        job_text = f"{job_data.title} {job_data.description} {' '.join(job_data.skills_required or [])}"
        
        # Generate vector embedding
        embeddings = parser.generate_embeddings(job_text)
        db_job.description_vector = embeddings
        
        # Save to database
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        logger.info(f"Created job posting: {db_job.id} - {db_job.title}")
        
        return JobResponse.from_orm(db_job)
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.get("/", response_model=List[JobResponse])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    remote_only: Optional[bool] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|title|company|salary_min)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List jobs with advanced filtering and search capabilities
    Requires: Authentication (any role)
    Returns: Only jobs from user's organization
    """
    try:
        # Organization isolation - only show active jobs from user's organization
        query = db.query(Job).filter(
            Job.status == "active",  # Use status field, not is_active property
            Job.organization_id == current_user.organization_id
        )
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Job.title.ilike(f"%{search}%"),
                    Job.description.ilike(f"%{search}%"),
                    Job.company_name.ilike(f"%{search}%")  # Use company_name field
                )
            )
        
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))
        
        if employment_type:
            query = query.filter(Job.job_type == employment_type)  # Use job_type field
        
        if experience_level:
            query = query.filter(Job.experience_level == experience_level)
        
        if remote_only:
            query = query.filter(Job.is_remote == True)  # Use is_remote field
        
        if salary_min:
            query = query.filter(Job.salary_min >= salary_min)
        
        if salary_max:
            query = query.filter(Job.salary_max <= salary_max)
        
        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Job, sort_by)))
        else:
            query = query.order_by(asc(getattr(Job, sort_by)))
        
        # Apply pagination
        jobs = query.offset(skip).limit(limit).all()
        
        return [JobResponse.from_orm(job) for job in jobs]
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific job by ID
    Requires: Authentication (any role)
    Returns: Job only if it belongs to user's organization
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.organization_id == current_user.organization_id  # Organization isolation
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.from_orm(job)

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"]))
):
    """
    Update existing job posting
    Requires: hr_manager or admin role
    """
    try:
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id  # Organization isolation
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update fields
        update_data = job_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(job, field, value)
        
        # Regenerate embeddings if description or requirements changed
        if 'description' in update_data or 'requirements' in update_data or 'skills_required' in update_data:
            parser = get_resume_parser()
            job_text = f"{job.title} {job.description} {' '.join(job.skills_required or [])}"
            embeddings = parser.generate_embeddings(job_text)
            job.description_vector = embeddings
        
        db.commit()
        db.refresh(job)
        
        logger.info(f"Updated job: {job_id}")
        return JobResponse.from_orm(job)
        
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")

@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"]))
):
    """
    Soft delete job posting (sets status to CLOSED)
    Requires: hr_manager or admin role
    """
    from app.models.job import JobStatus
    
    try:
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id  # Organization isolation
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Soft delete: Set status to CLOSED
        job.status = JobStatus.CLOSED
        db.commit()
        
        logger.info(f"Deleted (closed) job: {job_id}")
        return {"message": "Job deleted successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
        return {"message": "Job deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

@router.get("/{job_id}/candidates", response_model=List[Dict[str, Any]])
def get_matching_candidates(
    job_id: int,
    limit: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get candidates that match this job using advanced AI matching
    Requires: Authentication (recruiter or higher)
    """
    try:
        # Verify job exists and belongs to user's organization
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id  # Organization isolation
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get matching candidates using our research-based matching service
        candidates = job_matcher_service.find_best_candidates(job_id, db, limit)
        
        # Filter by minimum score
        filtered_candidates = [
            candidate for candidate in candidates 
            if candidate["score"] >= min_score
        ]
        
        logger.info(f"Found {len(filtered_candidates)} matching candidates for job {job_id}")
        return filtered_candidates
        
    except Exception as e:
        logger.error(f"Error finding candidates for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to find matching candidates: {str(e)}")

@router.post("/{job_id}/match/{candidate_id}")
def calculate_job_candidate_match(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate detailed match score between specific job and candidate
    Requires: Authentication (recruiter or higher)
    """
    try:
        # Verify job exists and belongs to user's organization
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id  # Organization isolation
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Calculate match score using advanced algorithm
        match_result = job_matcher_service.calculate_match_score(candidate_id, job_id, db)
        
        if "error" in match_result:
            raise HTTPException(status_code=400, detail=match_result["error"])
        
        return match_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating match between job {job_id} and candidate {candidate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate match: {str(e)}")

@router.get("/{job_id}/analytics")
def get_job_analytics(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "recruiter", "admin"]))
):
    """
    Get analytics and insights for a job posting
    Requires: hr_manager, recruiter, or admin role
    """
    try:
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id  # Organization isolation
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Basic analytics
        total_candidates = db.query(Candidate).count()
        
        # Get match scores for all candidates
        all_candidates = job_matcher_service.find_best_candidates(job_id, db, total_candidates)
        
        analytics = {
            "job_id": job_id,
            "total_candidates_in_system": total_candidates,
            "candidates_analyzed": len(all_candidates),
            "match_score_distribution": {
                "excellent": len([c for c in all_candidates if c["score"] >= 0.8]),
                "good": len([c for c in all_candidates if 0.6 <= c["score"] < 0.8]),
                "fair": len([c for c in all_candidates if 0.4 <= c["score"] < 0.6]),
                "poor": len([c for c in all_candidates if c["score"] < 0.4])
            },
            "average_match_score": sum(c["score"] for c in all_candidates) / len(all_candidates) if all_candidates else 0,
            "top_matching_skills": _get_top_matching_skills(all_candidates),
            "recommendations": _generate_job_recommendations(job, all_candidates)
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating analytics for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")

def _get_top_matching_skills(candidates: List[Dict[str, Any]]) -> List[str]:
    """
    Extract top skills from matching candidates
    """
    # This would analyze the top candidates' skills
    # Simplified implementation for now
    return ["Python", "JavaScript", "SQL", "React", "Node.js"]

def _generate_job_recommendations(job: Job, candidates: List[Dict[str, Any]]) -> List[str]:
    """
    Generate recommendations to improve job posting
    """
    recommendations = []
    
    if not candidates:
        recommendations.append("No matching candidates found. Consider broadening job requirements.")
    elif len([c for c in candidates if c["score"] >= 0.7]) < 3:
        recommendations.append("Few high-quality matches. Consider adjusting required skills or experience level.")
    
    if job.salary_min and job.salary_min < 50000:
        recommendations.append("Salary range might be below market rate for this role.")
    
    return recommendations