"""
AI Screening API Endpoints
Handles AI-powered candidate screening and evaluation
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.models.screening import Screening, ScreeningStatus
from app.models.job import Job
from app.models.candidate import Candidate
from app.services.ai_screening import ai_screening_service, QuestionType

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screening", tags=["AI Screening"])

# Request/Response Models
class StartScreeningRequest(BaseModel):
    job_id: int = Field(..., description="Job ID for the screening")
    candidate_id: int = Field(..., description="Candidate ID for the screening")
    num_questions: int = Field(5, ge=3, le=15, description="Number of questions to generate")
    question_types: Optional[List[QuestionType]] = Field(None, description="Types of questions to include")

class SubmitResponseRequest(BaseModel):
    question_id: str = Field(..., description="Question ID")
    response: str = Field(..., min_length=10, max_length=2000, description="Candidate's response")

class ScreeningResponse(BaseModel):
    screening_id: int
    questions: List[Dict[str, Any]]
    job_title: str
    candidate_name: str
    estimated_duration: int

class EvaluationResponse(BaseModel):
    evaluation: Dict[str, Any]
    progress: str
    completed: bool
    overall_score: Optional[float]

@router.post("/start", response_model=ScreeningResponse)
async def start_screening(
    request: StartScreeningRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new AI screening session for a candidate
    """
    try:
        # Verify job and candidate exist
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Check if screening already exists
        existing_screening = db.query(Screening).filter(
            Screening.job_id == request.job_id,
            Screening.candidate_id == request.candidate_id,
            Screening.status.in_([ScreeningStatus.IN_PROGRESS, ScreeningStatus.COMPLETED])
        ).first()
        
        if existing_screening:
            if existing_screening.status == ScreeningStatus.COMPLETED:
                raise HTTPException(
                    status_code=409, 
                    detail="Screening already completed for this job and candidate"
                )
            else:
                # Return existing in-progress screening
                return ScreeningResponse(
                    screening_id=existing_screening.id,
                    questions=existing_screening.questions,
                    job_title=job.title,
                    candidate_name=candidate.full_name,
                    estimated_duration=len(existing_screening.questions) * 3
                )
        
        # Generate new screening questions
        result = await ai_screening_service.generate_screening_questions(
            job_id=request.job_id,
            candidate_id=request.candidate_id,
            db=db,
            num_questions=request.num_questions,
            question_types=request.question_types
        )
        
        logger.info(f"Started screening {result['screening_id']} for candidate {request.candidate_id}")
        
        return ScreeningResponse(**result)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error starting screening: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start screening: {str(e)}")

@router.post("/{screening_id}/response", response_model=EvaluationResponse)
async def submit_response(
    screening_id: int,
    request: SubmitResponseRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a candidate's response to a screening question
    """
    try:
        # Verify screening exists and is in progress
        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise HTTPException(status_code=404, detail="Screening not found")
        
        if screening.status != ScreeningStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=409, 
                detail=f"Screening is not in progress (status: {screening.status})"
            )
        
        # Evaluate the response
        result = await ai_screening_service.evaluate_response(
            screening_id=screening_id,
            question_id=request.question_id,
            response=request.response,
            db=db
        )
        
        logger.info(f"Evaluated response for screening {screening_id}, question {request.question_id}")
        
        return EvaluationResponse(**result)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error submitting response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate response: {str(e)}")

@router.get("/{screening_id}", response_model=Dict[str, Any])
def get_screening(screening_id: int, db: Session = Depends(get_db)):
    """
    Get screening details and current status
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    
    job = db.query(Job).filter(Job.id == screening.job_id).first()
    candidate = db.query(Candidate).filter(Candidate.id == screening.candidate_id).first()
    
    return {
        "screening_id": screening.id,
        "job_title": job.title if job else "Unknown",
        "candidate_name": candidate.full_name if candidate else "Unknown",
        "status": screening.status,
        "questions": screening.questions,
        "responses": screening.responses or [],
        "overall_score": screening.overall_score,
        "created_at": screening.created_at,
        "completed_at": screening.completed_at,
        "progress": {
            "answered": len(screening.responses or []),
            "total": len(screening.questions),
            "percentage": round((len(screening.responses or []) / len(screening.questions)) * 100, 1) if screening.questions else 0
        }
    }

@router.get("/{screening_id}/summary", response_model=Dict[str, Any])
async def get_screening_summary(screening_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive screening summary with AI insights
    """
    try:
        summary = await ai_screening_service.get_screening_summary(screening_id, db)
        return summary
        
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error getting screening summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

@router.get("/job/{job_id}/screenings", response_model=List[Dict[str, Any]])
def list_job_screenings(
    job_id: int,
    status: Optional[ScreeningStatus] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all screenings for a specific job
    """
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    query = db.query(Screening).filter(Screening.job_id == job_id)
    
    if status:
        query = query.filter(Screening.status == status)
    
    screenings = query.offset(offset).limit(limit).all()
    
    results = []
    for screening in screenings:
        candidate = db.query(Candidate).filter(Candidate.id == screening.candidate_id).first()
        
        results.append({
            "screening_id": screening.id,
            "candidate_id": screening.candidate_id,
            "candidate_name": candidate.full_name if candidate else "Unknown",
            "candidate_email": candidate.email if candidate else "Unknown",
            "status": screening.status,
            "overall_score": screening.overall_score,
            "questions_count": len(screening.questions),
            "responses_count": len(screening.responses or []),
            "created_at": screening.created_at,
            "completed_at": screening.completed_at
        })
    
    return results

@router.get("/candidate/{candidate_id}/screenings", response_model=List[Dict[str, Any]])
def list_candidate_screenings(
    candidate_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all screenings for a specific candidate
    """
    # Verify candidate exists
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    screenings = db.query(Screening).filter(
        Screening.candidate_id == candidate_id
    ).offset(offset).limit(limit).all()
    
    results = []
    for screening in screenings:
        job = db.query(Job).filter(Job.id == screening.job_id).first()
        
        results.append({
            "screening_id": screening.id,
            "job_id": screening.job_id,
            "job_title": job.title if job else "Unknown",
            "job_company": job.company if job else "Unknown",
            "status": screening.status,
            "overall_score": screening.overall_score,
            "questions_count": len(screening.questions),
            "responses_count": len(screening.responses or []),
            "created_at": screening.created_at,
            "completed_at": screening.completed_at
        })
    
    return results

@router.delete("/{screening_id}")
def delete_screening(screening_id: int, db: Session = Depends(get_db)):
    """
    Delete a screening record (admin only)
    """
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    
    db.delete(screening)
    db.commit()
    
    logger.info(f"Deleted screening {screening_id}")
    return {"message": "Screening deleted successfully"}

@router.get("/analytics/overview", response_model=Dict[str, Any])
def get_screening_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get screening analytics and metrics
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Date range
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Basic metrics
    total_screenings = db.query(Screening).filter(
        Screening.created_at >= start_date
    ).count()
    
    completed_screenings = db.query(Screening).filter(
        Screening.created_at >= start_date,
        Screening.status == ScreeningStatus.COMPLETED
    ).count()
    
    # Average score
    avg_score = db.query(func.avg(Screening.overall_score)).filter(
        Screening.created_at >= start_date,
        Screening.status == ScreeningStatus.COMPLETED,
        Screening.overall_score.isnot(None)
    ).scalar() or 0
    
    # Score distribution
    score_ranges = [
        ("Excellent (80-100)", 80, 100),
        ("Good (65-79)", 65, 79),
        ("Average (50-64)", 50, 64),
        ("Below Average (0-49)", 0, 49)
    ]
    
    score_distribution = {}
    for label, min_score, max_score in score_ranges:
        count = db.query(Screening).filter(
            Screening.created_at >= start_date,
            Screening.status == ScreeningStatus.COMPLETED,
            Screening.overall_score >= min_score,
            Screening.overall_score <= max_score
        ).count()
        score_distribution[label] = count
    
    # Completion rate
    completion_rate = (completed_screenings / total_screenings * 100) if total_screenings > 0 else 0
    
    return {
        "period_days": days,
        "total_screenings": total_screenings,
        "completed_screenings": completed_screenings,
        "completion_rate": round(completion_rate, 1),
        "average_score": round(avg_score, 1),
        "score_distribution": score_distribution,
        "insights": [
            f"Screened {total_screenings} candidates in the last {days} days",
            f"Average screening score: {avg_score:.1f}/100",
            f"Completion rate: {completion_rate:.1f}%"
        ]
    }