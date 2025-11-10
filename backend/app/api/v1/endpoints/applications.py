"""
Application API Endpoints

Handles job applications with human-in-the-loop controls.
Enables HR to track candidates through the hiring pipeline.

All endpoints require authentication and enforce organization isolation.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.db.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.user import User
from app.models.audit_log import AuditLog
from app.dependencies.auth import get_current_user, require_role
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatusUpdate,
    ApplicationReview,
    ApplicationResponse,
    ApplicationListResponse,
    PipelineAnalytics
)

router = APIRouter()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_to_audit(db: Session, action: str, entity_type: str, entity_id: int, changes: dict, user_id: Optional[int] = None):
    """Log action to audit trail"""
    audit_log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        changes=changes
        # created_at is auto-set by default in the model
    )
    db.add(audit_log)
    db.commit()


# ============================================================================
# CREATE APPLICATION
# ============================================================================

@router.post("/", response_model=ApplicationResponse, status_code=201)
async def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["recruiter", "hr_manager", "admin"]))
):
    """
    Create a new job application.
    
    **Required role:** recruiter, hr_manager, or admin
    
    - **job_id**: ID of the job being applied to
    - **candidate_id**: ID of the candidate applying
    - **resume_id**: Optional ID of the resume used
    - **cover_letter**: Optional cover letter text
    - **source**: Application source (e.g., 'linkedin', 'direct', 'referral')
    
    Returns the created application with AI matching scores (if available).
    
    **Organization isolation:** Verifies job and candidate belong to user's organization.
    """
    # Verify job exists and belongs to user's organization
    job = db.query(Job).filter(
        Job.id == application_data.job_id,
        Job.organization_id == current_user.organization_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {application_data.job_id} not found in your organization"
        )
    
    # Verify candidate exists and belongs to user's organization
    candidate = db.query(Candidate).filter(
        Candidate.id == application_data.candidate_id,
        Candidate.organization_id == current_user.organization_id
    ).first()
    
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate {application_data.candidate_id} not found in your organization"
        )
    
    # Check for duplicate application (same job + candidate)
    existing_application = db.query(Application).filter(
        Application.job_id == application_data.job_id,
        Application.candidate_id == application_data.candidate_id
    ).first()
    
    if existing_application:
        raise HTTPException(
            status_code=400,
            detail=f"Application already exists for candidate {application_data.candidate_id} and job {application_data.job_id}"
        )
    
    # Create application
    application = Application(
        job_id=application_data.job_id,
        candidate_id=application_data.candidate_id,
        resume_id=application_data.resume_id,
        cover_letter=application_data.cover_letter,
        source=application_data.source,
        status=ApplicationStatus.APPLIED,
        applied_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Log to audit trail
    log_to_audit(
        db=db,
        action="application_created",
        entity_type="application",
        entity_id=application.id,
        changes={
            "job_id": application.job_id,
            "candidate_id": application.candidate_id,
            "status": application.status.value
        },
        user_id=current_user.id
    )
    
    # TODO: Trigger AI matching in background (calculate scores)
    # TODO: Trigger AI screening if configured
    
    return application


# ============================================================================
# READ APPLICATIONS
# ============================================================================

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single application by ID.
    
    **Required:** authenticated user
    
    Returns full application details including:
    - AI matching scores
    - AI recommendations with reasoning
    - Human review decisions
    - Pipeline status
    
    **Organization isolation:** Only applications from user's organization are accessible.
    """
    # JOIN with Job to filter by organization_id
    application = db.query(Application)\
        .join(Job, Application.job_id == Job.id)\
        .filter(
            Application.id == application_id,
            Job.organization_id == current_user.organization_id
        ).first()
    
    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found in your organization"
        )
    
    return application


@router.get("/job/{job_id}", response_model=ApplicationListResponse)
async def list_applications_by_job(
    job_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all applications for a specific job (paginated).
    
    **Required:** authenticated user
    
    Useful for HR to see all candidates who applied to a job.
    
    - **job_id**: ID of the job
    - **page**: Page number (default 1)
    - **page_size**: Items per page (default 20, max 100)
    - **status**: Optional filter by status (e.g., 'screening_passed')
    
    **Organization isolation:** Only shows applications for jobs in user's organization.
    """
    # First verify the job exists and belongs to user's organization
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.organization_id == current_user.organization_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found in your organization"
        )
    
    # Query applications for this job
    query = db.query(Application).filter(Application.job_id == job_id)
    
    if status:
        query = query.filter(Application.status == status)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    applications = query.order_by(Application.applied_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()
    
    return ApplicationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        applications=applications
    )


@router.get("/candidate/{candidate_id}", response_model=List[ApplicationResponse])
async def list_applications_by_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all applications from a specific candidate.
    
    **Required:** authenticated user
    
    Useful to see a candidate's application history.
    
    **Organization isolation:** Only shows applications for candidates in user's organization.
    """
    # First verify candidate exists and belongs to user's organization
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == current_user.organization_id
    ).first()
    
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate {candidate_id} not found in your organization"
        )
    
    # Get all applications for this candidate
    applications = db.query(Application) \
        .filter(Application.candidate_id == candidate_id) \
        .order_by(Application.applied_at.desc()) \
        .all()
    
    return applications


# ============================================================================
# UPDATE APPLICATION STATUS
# ============================================================================

@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["recruiter", "hr_manager", "admin"]))
):
    """
    Update application status (move through pipeline).
    
    **Required role:** recruiter, hr_manager, or admin
    
    Pipeline transitions:
    - applied → screening → screening_passed/screening_failed
    - screening_passed → interview_scheduled → interview_completed
    - interview_completed → shortlisted → offer_extended
    - offer_extended → offer_accepted/offer_rejected
    - Any status → rejected/withdrawn
    
    Logs all status changes to audit trail.
    
    **Organization isolation:** Only applications from user's organization can be updated.
    """
    # JOIN with Job to filter by organization_id
    application = db.query(Application)\
        .join(Job, Application.job_id == Job.id)\
        .filter(
            Application.id == application_id,
            Job.organization_id == current_user.organization_id
        ).first()
    
    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found in your organization"
        )
    
    old_status = application.status
    new_status = status_update.status
    
    # Update status
    application.status = new_status
    application.updated_at = datetime.utcnow()
    
    # Handle rejection
    if new_status == ApplicationStatus.REJECTED:
        application.rejected_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    
    # Log to audit trail
    log_to_audit(
        db=db,
        action="status_updated",
        entity_type="application",
        entity_id=application.id,
        changes={
            "old_status": old_status.value,
            "new_status": new_status.value,
            "notes": status_update.notes
        },
        user_id=current_user.id
    )
    
    # TODO: Trigger notifications (email, Slack, etc.)
    # TODO: Trigger n8n workflows based on status change
    
    return application


# ============================================================================
# HUMAN REVIEW (CRITICAL: Human-in-the-Loop Override)
# ============================================================================

@router.put("/{application_id}/review", response_model=ApplicationResponse)
async def review_application(
    application_id: int,
    review: ApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hiring_manager", "recruiter", "hr_manager", "admin"]))
):
    """
    HR reviews application and makes final decision.
    
    **Required role:** hiring_manager, recruiter, hr_manager, or admin
    
    **CRITICAL: This enables human-in-the-loop control.**
    
    HR can:
    - Override AI recommendations
    - Approve candidates AI marked as weak_fit
    - Reject candidates AI marked as strong_fit
    - Document reasoning (required)
    
    All reviews are logged to audit trail for compliance.
    
    - **human_decision**: 'approve', 'reject', or 'pending'
    - **human_notes**: Required reasoning (min 10 chars)
    - **rejection_reason**: Required if rejecting
    - **rejection_category**: Optional categorization
    
    **Organization isolation:** Only applications from user's organization can be reviewed.
    """
    # JOIN with Job to filter by organization_id
    application = db.query(Application)\
        .join(Job, Application.job_id == Job.id)\
        .filter(
            Application.id == application_id,
            Job.organization_id == current_user.organization_id
        ).first()
    
    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found in your organization"
        )
    
    # Store old values for audit log
    old_decision = application.human_decision
    ai_recommendation = application.ai_recommendation
    
    # Update human review fields
    application.human_decision = review.human_decision
    application.human_notes = review.human_notes
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = current_user.id
    
    # Handle rejection
    if review.human_decision == 'reject':
        application.rejection_reason = review.rejection_reason
        application.rejection_category = review.rejection_category
        application.rejected_at = datetime.utcnow()
        application.status = ApplicationStatus.REJECTED
    
    application.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    
    # Check if HR overrode AI recommendation
    override = False
    if ai_recommendation:
        if review.human_decision == 'approve' and ai_recommendation in ['weak_fit', 'no_fit']:
            override = True
        elif review.human_decision == 'reject' and ai_recommendation in ['strong_fit', 'good_fit']:
            override = True
    
    # Log to audit trail
    log_to_audit(
        db=db,
        action="human_review",
        entity_type="application",
        entity_id=application.id,
        changes={
            "old_decision": old_decision,
            "new_decision": review.human_decision,
            "ai_recommendation": ai_recommendation,
            "override": override,
            "notes": review.human_notes,
            "rejection_reason": review.rejection_reason
        },
        user_id=current_user.id
    )
    
    # TODO: Trigger notifications to candidate
    # TODO: If approved, trigger next step (interview scheduling)
    
    return application


# ============================================================================
# PIPELINE ANALYTICS
# ============================================================================

@router.get("/analytics/pipeline", response_model=PipelineAnalytics)
async def get_pipeline_analytics(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"]))
):
    """
    Get pipeline analytics and metrics.
    
    **Required role:** hr_manager or admin
    
    Returns:
    - Total applications
    - Distribution by status
    - Conversion rates (applied → screening → interview → offer)
    - Time metrics (avg time to screen, interview, hire)
    - AI performance (recommendation distribution, human override rate)
    
    Can be filtered by job (within user's organization).
    
    **Organization isolation:** Only shows analytics for user's organization.
    """
    # Base query with organization filter via JOIN
    query = db.query(Application)\
        .join(Job, Application.job_id == Job.id)\
        .filter(Job.organization_id == current_user.organization_id)
    
    # Optional job filter (already org-filtered)
    if job_id:
        # Verify job belongs to user's organization
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found in your organization"
            )
        
        query = query.filter(Application.job_id == job_id)
    
    # Total applications
    total_applications = query.count()
    
    # By status
    by_status = {}
    for status in ApplicationStatus:
        count = query.filter(Application.status == status).count()
        by_status[status.value] = count
    
    # Conversion rates
    applied_count = by_status.get('applied', 0) + by_status.get('screening', 0) + \
                    by_status.get('screening_passed', 0) + by_status.get('screening_failed', 0) + \
                    by_status.get('interview_scheduled', 0) + by_status.get('interview_completed', 0) + \
                    by_status.get('shortlisted', 0) + by_status.get('offer_extended', 0) + \
                    by_status.get('offer_accepted', 0) + by_status.get('offer_rejected', 0)
    
    screening_passed_count = by_status.get('screening_passed', 0) + \
                            by_status.get('interview_scheduled', 0) + \
                            by_status.get('interview_completed', 0) + \
                            by_status.get('shortlisted', 0) + \
                            by_status.get('offer_extended', 0) + \
                            by_status.get('offer_accepted', 0)
    
    interview_completed_count = by_status.get('interview_completed', 0) + \
                               by_status.get('shortlisted', 0) + \
                               by_status.get('offer_extended', 0) + \
                               by_status.get('offer_accepted', 0)
    
    offer_extended_count = by_status.get('offer_extended', 0) + by_status.get('offer_accepted', 0)
    
    screening_conversion_rate = (screening_passed_count / applied_count * 100) if applied_count > 0 else 0
    interview_conversion_rate = (interview_completed_count / screening_passed_count * 100) if screening_passed_count > 0 else 0
    offer_conversion_rate = (offer_extended_count / interview_completed_count * 100) if interview_completed_count > 0 else 0
    
    # AI recommendation distribution
    ai_recommendation_distribution = {
        'strong_fit': query.filter(Application.ai_recommendation == 'strong_fit').count(),
        'good_fit': query.filter(Application.ai_recommendation == 'good_fit').count(),
        'weak_fit': query.filter(Application.ai_recommendation == 'weak_fit').count(),
        'no_fit': query.filter(Application.ai_recommendation == 'no_fit').count()
    }
    
    # Human override rate
    total_reviewed = query.filter(Application.human_decision.isnot(None)).count()
    overrides = 0
    
    if total_reviewed > 0:
        # Count overrides (approve when AI said weak/no_fit, or reject when AI said strong/good_fit)
        overrides += query.filter(
            and_(
                Application.human_decision == 'approve',
                or_(Application.ai_recommendation == 'weak_fit', Application.ai_recommendation == 'no_fit')
            )
        ).count()
        
        overrides += query.filter(
            and_(
                Application.human_decision == 'reject',
                or_(Application.ai_recommendation == 'strong_fit', Application.ai_recommendation == 'good_fit')
            )
        ).count()
    
    human_override_rate = (overrides / total_reviewed * 100) if total_reviewed > 0 else 0
    
    # TODO: Calculate time metrics (requires timestamp analysis)
    
    return PipelineAnalytics(
        total_applications=total_applications,
        by_status=by_status,
        screening_conversion_rate=round(screening_conversion_rate, 1),
        interview_conversion_rate=round(interview_conversion_rate, 1),
        offer_conversion_rate=round(offer_conversion_rate, 1),
        avg_time_to_screen=None,  # TODO: Calculate from timestamps
        avg_time_to_interview=None,  # TODO: Calculate
        avg_time_to_hire=None,  # TODO: Calculate
        ai_recommendation_distribution=ai_recommendation_distribution,
        human_override_rate=round(human_override_rate, 1)
    )


# ============================================================================
# DELETE APPLICATION
# ============================================================================

@router.delete("/{application_id}", status_code=204)
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"]))
):
    """
    Delete (withdraw) an application.
    
    **Required role:** hr_manager or admin
    
    Sets status to WITHDRAWN and logs to audit trail.
    Soft delete - doesn't actually remove from database.
    
    **Organization isolation:** Only applications from user's organization can be deleted.
    """
    # JOIN with Job to filter by organization_id
    application = db.query(Application)\
        .join(Job, Application.job_id == Job.id)\
        .filter(
            Application.id == application_id,
            Job.organization_id == current_user.organization_id
        ).first()
    
    if not application:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found in your organization"
        )
    
    old_status = application.status
    
    # Soft delete - mark as withdrawn
    application.status = ApplicationStatus.WITHDRAWN
    application.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Log to audit trail
    log_to_audit(
        db=db,
        action="application_withdrawn",
        entity_type="application",
        entity_id=application.id,
        changes={
            "old_status": old_status.value,
            "new_status": ApplicationStatus.WITHDRAWN.value
        },
        user_id=current_user.id
    )
    
    return None
