"""
Comprehensive Interview API Tests
Tests all 10 Interview endpoints with various scenarios
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.models.interview import InterviewStatus, SessionState
from app.models.candidate import CandidateStatus


class TestInterviewCRUD:
    """Test basic CRUD operations for Interview API"""
    
    def test_create_interview_success(self, client, sample_candidate, sample_job, sample_organization):
        """Test successful interview creation"""
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        payload = {
            "candidate_id": sample_candidate.id,
            "job_id": sample_job.id,
            "interview_type": "voice",
            "platform": "twilio",
            "scheduled_at": scheduled_time,
            "duration_minutes": 30,
            "organization_id": sample_organization.id
        }
        
        response = client.post("/api/v1/interviews/", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["candidate_id"] == sample_candidate.id
        assert data["job_id"] == sample_job.id
        assert data["interview_type"] == "voice"
        assert data["status"] == "scheduled"
        assert data["session_state"] == "scheduled"
        assert data["organization_id"] == sample_organization.id
    
    def test_create_interview_with_application(self, client, sample_candidate, sample_job, sample_application, sample_organization):
        """Test interview creation linked to application"""
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        
        payload = {
            "candidate_id": sample_candidate.id,
            "job_id": sample_job.id,
            "application_id": sample_application.id,
            "interview_type": "video",
            "platform": "zoom",
            "scheduled_at": scheduled_time,
            "duration_minutes": 45,
            "organization_id": sample_organization.id
        }
        
        response = client.post("/api/v1/interviews/", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["application_id"] == sample_application.id
        assert data["platform"] == "zoom"
        assert data["duration_minutes"] == 45
    
    def test_get_interview_by_id(self, client, sample_interview):
        """Test retrieving single interview by ID"""
        response = client.get(f"/api/v1/interviews/{sample_interview.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_interview.id
        assert data["candidate_id"] == sample_interview.candidate_id
        assert data["job_id"] == sample_interview.job_id
    
    def test_get_interview_not_found(self, client):
        """Test 404 for non-existent interview"""
        response = client.get("/api/v1/interviews/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_interviews_empty(self, client):
        """Test listing interviews when none exist"""
        response = client.get("/api/v1/interviews/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["interviews"] == []
    
    def test_list_interviews_with_data(self, client, sample_interview):
        """Test listing interviews with pagination"""
        response = client.get("/api/v1/interviews/?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["interviews"]) == 1
        assert data["interviews"][0]["id"] == sample_interview.id
    
    def test_update_interview(self, client, sample_interview):
        """Test updating interview details"""
        payload = {
            "duration_minutes": 60,
            "interviewer_notes": "Updated notes for interview"
        }
        
        response = client.put(f"/api/v1/interviews/{sample_interview.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 60
        assert data["interviewer_notes"] == "Updated notes for interview"
    
    def test_delete_interview(self, client, sample_interview):
        """Test cancelling/deleting interview"""
        response = client.delete(f"/api/v1/interviews/{sample_interview.id}")
        
        assert response.status_code == 204
        
        # Verify it's cancelled (soft delete)
        get_response = client.get(f"/api/v1/interviews/{sample_interview.id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "cancelled"


class TestInterviewFiltering:
    """Test interview filtering and search functionality"""
    
    def test_filter_by_job_id(self, client, sample_interview, sample_job):
        """Test filtering interviews by job"""
        response = client.get(f"/api/v1/interviews/?job_id={sample_job.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(i["job_id"] == sample_job.id for i in data["interviews"])
    
    def test_filter_by_candidate_id(self, client, sample_interview, sample_candidate):
        """Test filtering interviews by candidate"""
        response = client.get(f"/api/v1/interviews/?candidate_id={sample_candidate.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(i["candidate_id"] == sample_candidate.id for i in data["interviews"])
    
    def test_filter_by_status(self, client, sample_interview):
        """Test filtering interviews by status"""
        response = client.get("/api/v1/interviews/?status=scheduled")
        
        assert response.status_code == 200
        data = response.json()
        assert all(i["status"] == "scheduled" for i in data["interviews"])
    
    def test_filter_by_interview_type(self, client, sample_interview):
        """Test filtering interviews by type"""
        response = client.get("/api/v1/interviews/?interview_type=voice")
        
        assert response.status_code == 200
        data = response.json()
        assert all(i["interview_type"] == "voice" for i in data["interviews"])
    
    def test_filter_by_organization(self, client, sample_interview, sample_organization):
        """Test filtering by organization (multi-tenant)"""
        response = client.get(f"/api/v1/interviews/?organization_id={sample_organization.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert all(i["organization_id"] == sample_organization.id for i in data["interviews"])
    
    def test_pagination(self, client, db_session, sample_candidate, sample_job, sample_organization):
        """Test pagination works correctly"""
        # Create 5 interviews
        from app.models.interview import Interview
        for i in range(5):
            interview = Interview(
                candidate_id=sample_candidate.id,
                job_id=sample_job.id,
                organization_id=sample_organization.id,
                interview_type="voice",
                platform="twilio",
                scheduled_at=datetime.utcnow() + timedelta(days=i+1),
                duration_minutes=30,
                status="scheduled",
                session_state="scheduled"
            )
            db_session.add(interview)
        db_session.commit()
        
        # Test pagination
        response = client.get("/api/v1/interviews/?skip=0&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["interviews"]) == 3
        
        # Second page
        response = client.get("/api/v1/interviews/?skip=3&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["interviews"]) == 2


class TestInterviewStatusTransitions:
    """Test interview status state machine"""
    
    def test_update_status_scheduled_to_in_progress(self, client, sample_interview):
        """Test valid transition from scheduled to in_progress"""
        payload = {
            "status": "in_progress",
            "notes": "Interview started"
        }
        
        response = client.patch(f"/api/v1/interviews/{sample_interview.id}/status", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["started_at"] is not None
    
    def test_update_status_in_progress_to_completed(self, client, sample_interview, db_session):
        """Test valid transition from in_progress to completed"""
        # First move to in_progress
        sample_interview.status = "in_progress"
        sample_interview.started_at = datetime.utcnow()
        db_session.commit()
        
        payload = {
            "status": "completed",
            "notes": "Interview completed successfully"
        }
        
        response = client.patch(f"/api/v1/interviews/{sample_interview.id}/status", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["ended_at"] is not None
        assert data["actual_duration_seconds"] is not None
    
    def test_update_status_invalid_transition(self, client, sample_interview):
        """Test invalid status transition is rejected"""
        payload = {
            "status": "completed"  # Can't go from scheduled directly to completed
        }
        
        response = client.patch(f"/api/v1/interviews/{sample_interview.id}/status", json=payload)
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_cancel_from_any_status(self, client, sample_interview):
        """Test cancellation is allowed from any status"""
        payload = {
            "status": "cancelled",
            "notes": "Candidate requested cancellation"
        }
        
        response = client.patch(f"/api/v1/interviews/{sample_interview.id}/status", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"


class TestSessionControl:
    """Test real-time session control functionality"""
    
    def test_start_session(self, client, sample_interview):
        """Test starting an interview session"""
        payload = {"action": "start"}
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/session", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_state"] == "in_progress"
        assert data["status"] == "in_progress"
        assert data["started_at"] is not None
        assert data["last_activity_at"] is not None
    
    def test_pause_session(self, client, sample_interview, db_session):
        """Test pausing an active session"""
        # First start the session
        sample_interview.start_session()
        db_session.commit()
        
        payload = {
            "action": "pause",
            "reason": "Candidate requested a break"
        }
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/session", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_state"] == "paused"
        assert data["pause_count"] == 1
        assert data["paused_at"] is not None
    
    def test_resume_session(self, client, sample_interview, db_session):
        """Test resuming a paused session"""
        # Start then pause
        sample_interview.start_session()
        sample_interview.pause_session()
        db_session.commit()
        
        payload = {"action": "resume"}
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/session", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_state"] == "in_progress"
        assert data["resumed_at"] is not None
    
    def test_complete_session(self, client, sample_interview, db_session):
        """Test completing a session"""
        # Start the session first
        sample_interview.start_session()
        db_session.commit()
        
        payload = {"action": "complete"}
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/session", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_state"] == "completed"
        assert data["status"] == "completed"
        assert data["ended_at"] is not None
    
    def test_abandon_session(self, client, sample_interview, db_session):
        """Test abandoning a session (no-show)"""
        # Start the session
        sample_interview.start_session()
        db_session.commit()
        
        payload = {
            "action": "abandon",
            "reason": "Candidate did not show up"
        }
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/session", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_state"] == "abandoned"
        assert data["status"] == "no_show"
    
    def test_invalid_session_action(self, client, sample_interview):
        """Test invalid session action is rejected"""
        payload = {"action": "invalid_action"}
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/session", json=payload)
        
        # Pydantic validation errors return 422, not 400
        assert response.status_code == 422
    
    def test_session_state_validation(self, client, sample_interview):
        """Test session state machine validation"""
        # Try to pause without starting
        payload = {"action": "pause"}
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/session", json=payload)
        
        assert response.status_code == 400
        assert "cannot pause" in response.json()["detail"].lower()


class TestHumanFeedback:
    """Test human-in-the-loop feedback functionality"""
    
    def test_add_feedback(self, client, sample_interview, sample_user):
        """Test adding interviewer feedback"""
        payload = {
            "interviewer_id": sample_user.id,
            "interviewer_notes": "Candidate showed excellent technical skills and clear communication.",
            "interviewer_rating": 9
        }
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/feedback", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["interviewer_id"] == sample_user.id
        assert data["interviewer_rating"] == 9
        assert "excellent technical skills" in data["interviewer_notes"]
    
    def test_feedback_validation(self, client, sample_interview, sample_user):
        """Test feedback validation rules"""
        # Rating must be 1-10
        payload = {
            "interviewer_id": sample_user.id,
            "interviewer_notes": "Short note",
            "interviewer_rating": 11  # Invalid
        }
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/feedback", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_feedback_override_detection(self, client, sample_interview, sample_user, db_session):
        """Test detection of human override of AI scores"""
        # Set AI score high
        sample_interview.overall_score = 85.0
        db_session.commit()
        
        # Human gives low rating (9*10=90 vs 85 = 5 point diff, not override)
        # Let's make AI score 50
        sample_interview.overall_score = 50.0
        db_session.commit()
        
        payload = {
            "interviewer_id": sample_user.id,
            "interviewer_notes": "Disagree with AI assessment - candidate is excellent",
            "interviewer_rating": 9  # 90 vs 50 = 40 point difference = override
        }
        
        response = client.post(f"/api/v1/interviews/{sample_interview.id}/feedback", json=payload)
        
        assert response.status_code == 200
        # Verify audit log captured the override (checked in audit log tests)


class TestAnalytics:
    """Test interview analytics endpoints"""
    
    def test_get_analytics_empty(self, client):
        """Test analytics with no interviews"""
        response = client.get("/api/v1/interviews/analytics/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_interviews"] == 0
        assert data["completion_rate"] == 0.0
    
    def test_get_analytics_with_data(self, client, db_session, sample_candidate, sample_job, sample_organization):
        """Test analytics with sample data"""
        from app.models.interview import Interview
        
        # Create multiple interviews with different statuses
        statuses = ["scheduled", "in_progress", "completed", "completed", "no_show"]
        for status in statuses:
            interview = Interview(
                candidate_id=sample_candidate.id,
                job_id=sample_job.id,
                organization_id=sample_organization.id,
                interview_type="voice",
                platform="twilio",
                scheduled_at=datetime.utcnow(),
                duration_minutes=30,
                status=status,
                session_state=status if status != "no_show" else "abandoned"
            )
            db_session.add(interview)
        db_session.commit()
        
        response = client.get("/api/v1/interviews/analytics/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_interviews"] == 5
        assert data["by_status"]["completed"] == 2
        assert data["by_status"]["scheduled"] == 1
        assert data["by_status"]["no_show"] == 1
        assert data["completion_rate"] == 40.0  # 2/5 = 40%
        assert data["no_show_rate"] == 20.0  # 1/5 = 20%
    
    def test_analytics_filter_by_organization(self, client, sample_interview, sample_organization):
        """Test analytics filtered by organization"""
        response = client.get(f"/api/v1/interviews/analytics/performance?organization_id={sample_organization.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_interviews"] >= 1
    
    def test_analytics_date_range(self, client, sample_interview):
        """Test analytics with date range filtering"""
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        response = client.get(
            f"/api/v1/interviews/analytics/performance?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation"""
    
    def test_organization_isolation(self, client, db_session, sample_candidate, sample_job):
        """Test that interviews are isolated by organization"""
        from app.models.organization import Organization
        from app.models.interview import Interview
        
        # Create second organization
        org2 = Organization(
            name="Other Agency",
            slug="other-agency",
            industry="Staffing",
            company_size="10-50",
            plan="basic",
            subscription_status="active"
        )
        db_session.add(org2)
        db_session.commit()
        
        # Create interview for org2
        interview_org2 = Interview(
            candidate_id=sample_candidate.id,
            job_id=sample_job.id,
            organization_id=org2.id,
            interview_type="voice",
            platform="twilio",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            status="scheduled",
            session_state="scheduled"
        )
        db_session.add(interview_org2)
        db_session.commit()
        
        # Filter by org1 - should not see org2's interview
        response = client.get(f"/api/v1/interviews/?organization_id={sample_job.organization_id}")
        data = response.json()
        
        for interview in data["interviews"]:
            assert interview["organization_id"] != org2.id


class TestGetInterviewsByCandidate:
    """Test retrieving interviews by candidate"""
    
    def test_get_candidate_interviews(self, client, sample_interview, sample_candidate):
        """Test getting all interviews for a candidate"""
        response = client.get(f"/api/v1/interviews/candidate/{sample_candidate.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(i["candidate_id"] == sample_candidate.id for i in data)
    
    def test_get_candidate_interviews_empty(self, client, sample_candidate, db_session):
        """Test getting interviews for candidate with no interviews"""
        from app.models.candidate import Candidate
        
        # Create new candidate with no interviews
        candidate = Candidate(
            organization_id=sample_candidate.organization_id,
            full_name="Jane Smith",
            email="jane.smith@example.com",
            status=CandidateStatus.NEW
        )
        db_session.add(candidate)
        db_session.commit()
        
        response = client.get(f"/api/v1/interviews/candidate/{candidate.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestInterviewWorkflow:
    """Test complete interview workflow end-to-end"""
    
    def test_full_interview_lifecycle(self, client, sample_candidate, sample_job, sample_application, sample_organization, sample_user):
        """Test complete interview workflow from creation to completion"""
        
        # 1. Create interview
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        create_payload = {
            "candidate_id": sample_candidate.id,
            "job_id": sample_job.id,
            "application_id": sample_application.id,
            "interview_type": "voice",
            "platform": "twilio",
            "scheduled_at": scheduled_time,
            "duration_minutes": 30,
            "organization_id": sample_organization.id
        }
        
        create_response = client.post("/api/v1/interviews/", json=create_payload)
        assert create_response.status_code == 201
        interview_id = create_response.json()["id"]
        
        # 2. Start session
        start_response = client.post(
            f"/api/v1/interviews/{interview_id}/session",
            json={"action": "start"}
        )
        assert start_response.status_code == 200
        assert start_response.json()["session_state"] == "in_progress"
        
        # 3. Pause session
        pause_response = client.post(
            f"/api/v1/interviews/{interview_id}/session",
            json={"action": "pause", "reason": "Technical issue"}
        )
        assert pause_response.status_code == 200
        assert pause_response.json()["pause_count"] == 1
        
        # 4. Resume session
        resume_response = client.post(
            f"/api/v1/interviews/{interview_id}/session",
            json={"action": "resume"}
        )
        assert resume_response.status_code == 200
        assert resume_response.json()["session_state"] == "in_progress"
        
        # 5. Complete session
        complete_response = client.post(
            f"/api/v1/interviews/{interview_id}/session",
            json={"action": "complete"}
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "completed"
        
        # 6. Add human feedback
        feedback_response = client.post(
            f"/api/v1/interviews/{interview_id}/feedback",
            json={
                "interviewer_id": sample_user.id,
                "interviewer_notes": "Excellent interview, strong candidate",
                "interviewer_rating": 9
            }
        )
        assert feedback_response.status_code == 200
        assert feedback_response.json()["interviewer_rating"] == 9
        
        # 7. Verify final state
        get_response = client.get(f"/api/v1/interviews/{interview_id}")
        final_data = get_response.json()
        assert final_data["status"] == "completed"
        assert final_data["session_state"] == "completed"
        assert final_data["pause_count"] == 1
        assert final_data["interviewer_rating"] == 9
