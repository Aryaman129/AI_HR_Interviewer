"""
Interview API Endpoints

Handles voice/video interviews with real-time session control.
Enables multi-tenant isolation and human-in-the-loop feedback.

All endpoints require authentication with role-based access control.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from uuid import uuid4

from app.db.database import get_db
from app.models.interview import Interview, InterviewStatus, SessionState
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.models.audit_log import AuditLog
from app.dependencies.auth import get_current_user, require_role
from app.schemas.interview import (
    InterviewCreate,
    InterviewUpdate,
    InterviewSessionControl,
    InterviewStatusUpdate,
    InterviewFeedback,
    InterviewResponse,
    InterviewListResponse,
    InterviewAnalytics
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
    )
    db.add(audit_log)
    db.commit()


# ============================================================================
# CREATE INTERVIEW
# ============================================================================

@router.post("/", response_model=InterviewResponse, status_code=201)
async def create_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["recruiter", "hr_manager", "admin"]))
):
    """
    Schedule a new interview session. Requires interviewer+ role.
    
    - **candidate_id**: ID of the candidate
    - **job_id**: ID of the job position
    - **application_id**: Optional ID of the application
    - **interview_type**: 'voice', 'video', or 'phone'
    - **platform**: 'twilio', 'zoom', 'teams', or 'manual'
    - **scheduled_at**: When the interview is scheduled
    - **duration_minutes**: Expected duration (default 30)
    
    All entities (candidate, job, application) must belong to your organization.
    Organization ID is automatically set from authenticated user.
    """
    # Verify candidate belongs to user's organization
    candidate = db.query(Candidate).filter(
        Candidate.id == interview_data.candidate_id,
        Candidate.organization_id == current_user.organization_id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found in your organization")
    
    # Verify job belongs to user's organization
    job = db.query(Job).filter(
        Job.id == interview_data.job_id,
        Job.organization_id == current_user.organization_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found in your organization")
    
    # If application_id provided, verify it belongs to user's organization
    if interview_data.application_id:
        application = db.query(Application).join(Job).filter(
            Application.id == interview_data.application_id,
            Job.organization_id == current_user.organization_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found in your organization")
    
    # Check for scheduling conflicts (same candidate, overlapping time)
    if interview_data.scheduled_at:
        conflict_start = interview_data.scheduled_at - timedelta(minutes=interview_data.duration_minutes or 30)
        conflict_end = interview_data.scheduled_at + timedelta(minutes=interview_data.duration_minutes or 30)
        
        conflict = db.query(Interview).filter(
            Interview.candidate_id == interview_data.candidate_id,
            Interview.organization_id == current_user.organization_id,
            Interview.scheduled_at.between(conflict_start, conflict_end),
            Interview.status.in_([InterviewStatus.SCHEDULED.value, InterviewStatus.IN_PROGRESS.value])
        ).first()
        
        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Scheduling conflict: Candidate has another interview at {conflict.scheduled_at}"
            )
    
    # Create interview with organization isolation
    interview = Interview(
        candidate_id=interview_data.candidate_id,
        job_id=interview_data.job_id,
        application_id=interview_data.application_id,
        interview_type=interview_data.interview_type,
        platform=interview_data.platform,
        scheduled_at=interview_data.scheduled_at,
        duration_minutes=interview_data.duration_minutes,
        organization_id=current_user.organization_id,  # Force user's org
        client_id=interview_data.client_id,
        interviewer_id=current_user.id,
        status=InterviewStatus.SCHEDULED.value,
        session_state=SessionState.SCHEDULED.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    # Log to audit trail with user context
    log_to_audit(
        db=db,
        action="interview_created",
        entity_type="interview",
        entity_id=interview.id,
        changes={
            "candidate_id": interview.candidate_id,
            "job_id": interview.job_id,
            "interview_type": interview.interview_type,
            "scheduled_at": interview.scheduled_at.isoformat() if interview.scheduled_at else None,
            "organization_id": interview.organization_id
        },
        user_id=current_user.id
    )
    
    # TODO: Trigger calendar invite/notification
    # TODO: Send confirmation email to candidate
    # TODO: Set up webhook for platform (Twilio/Zoom)
    
    return interview


# ============================================================================
# LIST INTERVIEWS
# ============================================================================

@router.get("/", response_model=InterviewListResponse)
async def list_interviews(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    candidate_id: Optional[int] = Query(None, description="Filter by candidate ID"),
    status: Optional[InterviewStatus] = Query(None, description="Filter by status"),
    interview_type: Optional[str] = Query(None, description="Filter by type (voice/video/phone)"),
    scheduled_after: Optional[datetime] = Query(None, description="Filter interviews scheduled after this date"),
    scheduled_before: Optional[datetime] = Query(None, description="Filter interviews scheduled before this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List interviews with pagination and filtering. Requires authentication.
    
    Automatically filtered by user's organization for security.
    Returns paginated results with total count.
    """
    query = db.query(Interview).filter(
        Interview.organization_id == current_user.organization_id
    )
    
    # Apply optional filters
    if job_id:
        # Verify job belongs to user's org
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found in your organization")
        query = query.filter(Interview.job_id == job_id)
    
    if candidate_id:
        # Verify candidate belongs to user's org
        candidate = db.query(Candidate).filter(
            Candidate.id == candidate_id,
            Candidate.organization_id == current_user.organization_id
        ).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found in your organization")
        query = query.filter(Interview.candidate_id == candidate_id)
    
    if status:
        query = query.filter(Interview.status == status.value)
    if interview_type:
        query = query.filter(Interview.interview_type == interview_type)
    if scheduled_after:
        query = query.filter(Interview.scheduled_at >= scheduled_after)
    if scheduled_before:
        query = query.filter(Interview.scheduled_at <= scheduled_before)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    interviews = query.order_by(Interview.scheduled_at.desc()) \
        .offset(skip) \
        .limit(limit) \
        .all()
    
    # Calculate page number from skip/limit
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return InterviewListResponse(
        total=total,
        page=page,
        page_size=limit,
        interviews=interviews
    )


# ============================================================================
# GET SINGLE INTERVIEW
# ============================================================================

@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single interview by ID. Requires authentication.
    
    Returns full interview details including:
    - Session state and tracking
    - Recording and transcript
    - AI analysis and scores
    - Human feedback and ratings
    
    Only accessible if interview belongs to your organization.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.organization_id == current_user.organization_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found in your organization")
    
    return interview


# ============================================================================
# UPDATE INTERVIEW
# ============================================================================

@router.put("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: int,
    update_data: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["recruiter", "hr_manager", "admin"]))
):
    """
    Update interview details (rescheduling, notes, etc.). Requires interviewer+ role.
    
    Supports partial updates. Only provided fields will be updated.
    Logs changes to audit trail with user context.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.organization_id == current_user.organization_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found in your organization")
    
    # Track changes for audit log
    changes = {}
    
    # Update fields (partial update)
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(interview, field):
            old_value = getattr(interview, field)
            if old_value != value:
                changes[field] = {"old": str(old_value), "new": str(value)}
                setattr(interview, field, value)
    
    interview.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(interview)
    
    # Log to audit trail if changes were made
    if changes:
        log_to_audit(
            db=db,
            action="interview_updated",
            entity_type="interview",
            entity_id=interview.id,
            changes=changes,
            user_id=current_user.id
        )
    
    return interview


# ============================================================================
# DELETE INTERVIEW
# ============================================================================

@router.delete("/{interview_id}", status_code=204)
async def delete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"]))
):
    """
    Cancel and delete an interview. Requires hr_manager+ role.
    
    Sets status to CANCELLED and logs to audit trail.
    Soft delete - marks as cancelled rather than removing.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.organization_id == current_user.organization_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found in your organization")
    
    old_status = interview.status
    
    # Soft delete - mark as cancelled
    interview.status = InterviewStatus.CANCELLED.value
    interview.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Log to audit trail with user context
    log_to_audit(
        db=db,
        action="interview_cancelled",
        entity_type="interview",
        entity_id=interview.id,
        changes={
            "old_status": old_status,
            "new_status": "cancelled"
        },
        user_id=current_user.id
    )
    
    return None


# ============================================================================
# UPDATE INTERVIEW STATUS
# ============================================================================

@router.patch("/{interview_id}/status", response_model=InterviewResponse)
async def update_interview_status(
    interview_id: int,
    status_update: InterviewStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hiring_manager", "recruiter", "hr_manager", "admin"]))
):
    """
    Update interview status with state machine validation. Requires interviewer+ role.
    
    Valid transitions:
    - scheduled → in_progress (when call starts)
    - in_progress → paused (temporary hold)
    - paused → in_progress (resume)
    - in_progress → completed (successful completion)
    - in_progress → no_show (candidate didn't show)
    - Any status → cancelled (manual cancellation)
    - scheduled → rescheduled (change date/time)
    
    Validates transitions and logs to audit trail.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.organization_id == current_user.organization_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found in your organization")
    
    old_status = interview.status
    new_status = status_update.status
    
    # Validate state transition
    valid_transitions = {
        InterviewStatus.SCHEDULED: [InterviewStatus.IN_PROGRESS, InterviewStatus.CANCELLED, InterviewStatus.RESCHEDULED, InterviewStatus.NO_SHOW],
        InterviewStatus.IN_PROGRESS: [InterviewStatus.PAUSED, InterviewStatus.COMPLETED, InterviewStatus.CANCELLED, InterviewStatus.NO_SHOW],
        InterviewStatus.PAUSED: [InterviewStatus.IN_PROGRESS, InterviewStatus.CANCELLED],
        InterviewStatus.RESCHEDULED: [InterviewStatus.SCHEDULED, InterviewStatus.CANCELLED]
    }
    
    if old_status in valid_transitions and new_status not in valid_transitions[old_status]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {old_status} to {new_status}"
        )
    
    # Update status
    interview.status = new_status.value
    interview.updated_at = datetime.utcnow()
    
    # Update timestamps based on status
    if new_status == InterviewStatus.IN_PROGRESS and not interview.started_at:
        interview.started_at = datetime.utcnow()
    elif new_status == InterviewStatus.COMPLETED:
        interview.ended_at = datetime.utcnow()
        if interview.started_at:
            interview.actual_duration_seconds = int((interview.ended_at - interview.started_at).total_seconds())
    elif new_status == InterviewStatus.CANCELLED:
        pass  # interview.cancelled_at = datetime.utcnow()  # TODO: Add field to model
    
    db.commit()
    db.refresh(interview)
    
    # Log to audit trail with user context
    log_to_audit(
        db=db,
        action="interview_status_updated",
        entity_type="interview",
        entity_id=interview.id,
        changes={
            "old_status": old_status,
            "new_status": new_status.value,
            "notes": status_update.notes
        },
        user_id=current_user.id
    )
    
    return interview


# ============================================================================
# SESSION CONTROL (Real-time pause/resume/complete)
# ============================================================================

@router.post("/{interview_id}/session", response_model=InterviewResponse)
async def control_session(
    interview_id: int,
    control: InterviewSessionControl,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hiring_manager", "hr_manager", "admin"]))
):
    """
    Real-time session control for active interviews. Requires interviewer+ role.
    
    Actions:
    - **start**: Begin the interview session
    - **pause**: Temporarily pause (e.g., candidate needs break)
    - **resume**: Resume from pause
    - **complete**: Successfully complete the session
    - **abandon**: Candidate left without completing
    
    Uses session state machine from Interview model.
    Tracks pause counts and activity timestamps.
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.organization_id == current_user.organization_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found in your organization")
    
    old_state = interview.session_state
    
    try:
        # Execute session control action using model methods
        if control.action == "start":
            interview.start_session()
        elif control.action == "pause":
            interview.pause_session()
        elif control.action == "resume":
            interview.resume_session()
        elif control.action == "complete":
            interview.complete_session()
        elif control.action == "abandon":
            interview.abandon_session()
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {control.action}")
        
        interview.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(interview)
        
        # Log to audit trail with user context
        log_to_audit(
            db=db,
            action=f"interview_session_{control.action}",
            entity_type="interview",
            entity_id=interview.id,
            changes={
                "old_state": old_state,
                "new_state": interview.session_state,
                "action": control.action,
                "notes": control.notes
            },
            user_id=current_user.id
        )
        
        return interview
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# HUMAN FEEDBACK (CRITICAL: Human-in-the-Loop Override)
# ============================================================================

@router.post("/{interview_id}/feedback", response_model=InterviewResponse)
async def add_feedback(
    interview_id: int,
    feedback: InterviewFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hiring_manager", "hr_manager", "admin"]))
):
    """
    Add human interviewer feedback and ratings. Requires interviewer+ role.
    
    **CRITICAL: This enables human-in-the-loop control.**
    
    Interviewer can:
    - Override AI scores and recommendations
    - Add qualitative notes and observations
    - Provide final rating (1-10)
    - Document specific concerns or strengths
    
    All feedback is logged to audit trail for compliance.
    Detects when human rating differs significantly from AI scores.
    
    - **interviewer_notes**: Detailed feedback (required, min 10 chars)
    - **interviewer_rating**: Rating 1-10 (required)
    """
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.organization_id == current_user.organization_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found in your organization")
    
    # Validate feedback notes
    if not feedback.interviewer_notes or len(feedback.interviewer_notes.strip()) < 10:
        raise HTTPException(status_code=400, detail="Interviewer notes must be at least 10 characters")
    
    # Store old values for audit log
    old_rating = interview.interviewer_rating
    ai_score = interview.overall_score
    
    # Update feedback fields (use authenticated user as interviewer)
    interview.interviewer_id = current_user.id
    interview.interviewer_notes = feedback.interviewer_notes
    interview.interviewer_rating = feedback.interviewer_rating
    interview.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(interview)
    
    # Detect if human rating differs significantly from AI score
    override = False
    if ai_score is not None:
        # Convert 1-10 rating to 0-100 scale for comparison
        human_score = feedback.interviewer_rating * 10
        score_diff = abs(human_score - ai_score)
        
        # Flag as override if difference > 20 points
        if score_diff > 20:
            override = True
    
    # Log to audit trail with override detection
    log_to_audit(
        db=db,
        action="interview_feedback_added",
        entity_type="interview",
        entity_id=interview.id,
        changes={
            "interviewer_rating": feedback.interviewer_rating,
            "old_rating": old_rating,
            "ai_overall_score": ai_score,
            "override_detected": override,
            "notes_length": len(feedback.interviewer_notes)
        },
        user_id=current_user.id
    )
    
    return interview


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/analytics/performance", response_model=InterviewAnalytics)
async def get_analytics(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["hr_manager", "admin"]))
):
    """
    Get comprehensive interview analytics and metrics. Requires hr_manager+ role.
    
    Automatically filtered by user's organization for security.
    
    Returns:
    - Total interviews conducted
    - Distribution by status and type
    - Completion and no-show rates
    - Average scores (AI and human)
    - Session pause rate and duration metrics
    - Human override rate (when interviewer disagrees with AI)
    
    Can be filtered by job and date range.
    """
    query = db.query(Interview).filter(
        Interview.organization_id == current_user.organization_id
    )
    
    if job_id:
        # Verify job belongs to user's org
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == current_user.organization_id
        ).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found in your organization")
        query = query.filter(Interview.job_id == job_id)
    
    if start_date:
        query = query.filter(Interview.created_at >= start_date)
    
    if end_date:
        query = query.filter(Interview.created_at <= end_date)
    
    # Total interviews
    total_interviews = query.count()
    
    # By status
    by_status = {}
    for status in InterviewStatus:
        count = query.filter(Interview.status == status.value).count()
        by_status[status.value] = count
    
    # By session state
    by_session_state = {}
    for session_state in ["scheduled", "in_progress", "paused", "completed", "abandoned"]:
        count = query.filter(Interview.session_state == session_state).count()
        by_session_state[session_state] = count
    
    # By type
    by_type = {}
    for interview_type in ["voice", "video", "phone"]:
        count = query.filter(Interview.interview_type == interview_type).count()
        if count > 0:
            by_type[interview_type] = count
    
    # By platform
    by_platform = {}
    for platform in ["twilio", "zoom", "teams", "manual"]:
        count = query.filter(Interview.platform == platform).count()
        if count > 0:
            by_platform[platform] = count
    
    # Completion rate
    completed_count = by_status.get('completed', 0)
    completion_rate = (completed_count / total_interviews * 100) if total_interviews > 0 else 0
    
    # No-show rate
    no_show_count = by_status.get('no_show', 0)
    no_show_rate = (no_show_count / total_interviews * 100) if total_interviews > 0 else 0
    
    # Cancellation rate
    cancelled_count = by_status.get('cancelled', 0)
    cancellation_rate = (cancelled_count / total_interviews * 100) if total_interviews > 0 else 0
    
    # Average scores (only for completed interviews)
    completed_interviews = query.filter(Interview.status == InterviewStatus.COMPLETED.value)
    
    avg_overall_score = db.query(func.avg(Interview.overall_score)) \
        .filter(Interview.id.in_([i.id for i in completed_interviews.all()])) \
        .scalar() or 0.0
    
    avg_technical_score = db.query(func.avg(Interview.technical_score)) \
        .filter(Interview.id.in_([i.id for i in completed_interviews.all()])) \
        .scalar() or 0.0
    
    avg_communication_score = db.query(func.avg(Interview.communication_score)) \
        .filter(Interview.id.in_([i.id for i in completed_interviews.all()])) \
        .scalar() or 0.0
    
    # Human feedback metrics
    interviews_with_feedback = query.filter(Interview.interviewer_rating.isnot(None)).count()
    feedback_rate = (interviews_with_feedback / total_interviews * 100) if total_interviews > 0 else 0
    
    avg_human_rating = db.query(func.avg(Interview.interviewer_rating)) \
        .filter(Interview.id.in_([i.id for i in query.all()])) \
        .scalar() or 0.0
    
    # Session pause metrics
    sessions_with_pauses = query.filter(Interview.pause_count > 0).count()
    pause_rate = (sessions_with_pauses / total_interviews * 100) if total_interviews > 0 else 0
    
    avg_pause_count = db.query(func.avg(Interview.pause_count)) \
        .filter(Interview.id.in_([i.id for i in query.all()])) \
        .scalar() or 0.0
    
    # AI recommendation distribution
    ai_recommendation_distribution = {}
    for recommendation in ["strong_hire", "hire", "maybe", "no_hire"]:
        count = query.filter(Interview.ai_recommendation == recommendation).count()
        if count > 0:
            ai_recommendation_distribution[recommendation] = count
    
    # Average duration (for completed interviews)
    avg_duration_seconds = db.query(func.avg(Interview.actual_duration_seconds)) \
        .filter(Interview.id.in_([i.id for i in completed_interviews.all()])) \
        .scalar() or 0.0
    
    return InterviewAnalytics(
        total_interviews=total_interviews,
        by_status=by_status,
        by_session_state=by_session_state,
        by_type=by_type,
        by_platform=by_platform,
        completion_rate=round(completion_rate, 1),
        no_show_rate=round(no_show_rate, 1),
        cancellation_rate=round(cancellation_rate, 1),
        avg_pause_count=round(avg_pause_count, 2),
        sessions_with_pauses=sessions_with_pauses,
        pause_rate=round(pause_rate, 1),
        avg_overall_score=round(avg_overall_score, 1),
        avg_technical_score=round(avg_technical_score, 1),
        avg_communication_score=round(avg_communication_score, 1),
        avg_human_rating=round(avg_human_rating, 1),
        interviews_with_feedback=interviews_with_feedback,
        feedback_rate=round(feedback_rate, 1),
        ai_recommendation_distribution=ai_recommendation_distribution,
        avg_duration_minutes=round(avg_duration_seconds / 60, 1) if avg_duration_seconds > 0 else 0.0
    )


# ============================================================================
# GET INTERVIEWS BY CANDIDATE
# ============================================================================

@router.get("/candidate/{candidate_id}", response_model=List[InterviewResponse])
async def get_interviews_by_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all interviews for a specific candidate. Requires authentication.
    
    Useful to see a candidate's interview history across multiple jobs.
    Returns interviews ordered by scheduled date (most recent first).
    
    Candidate must belong to your organization.
    """
    # Verify candidate belongs to user's organization
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.organization_id == current_user.organization_id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found in your organization")
    
    # Get all interviews for this candidate in user's org
    interviews = db.query(Interview).filter(
        Interview.candidate_id == candidate_id,
        Interview.organization_id == current_user.organization_id
    ).order_by(Interview.scheduled_at.desc()).all()
    
    return interviews
