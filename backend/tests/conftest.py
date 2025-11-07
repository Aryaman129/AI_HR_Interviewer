"""
Pytest Configuration and Fixtures
Provides test database setup, client fixtures, and common test utilities
"""
import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from fastapi.testclient import TestClient
import httpx

from app.main import app
from app.db.database import Base, get_db
from app.core.config import settings


# ============================================================================
# JSONB COMPATIBILITY FOR SQLITE
# ============================================================================
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    """Compile JSONB as JSON for SQLite in tests"""
    return "JSON"


# ============================================================================
# TEST DATABASE SETUP
# ============================================================================

@pytest.fixture(scope="session")
def test_db_url():
    """Test database URL.

    By default tests use SQLite in-memory for fast, hermetic unit tests.
    To run production-like integration tests against PostgreSQL, set
    the environment variable `USE_POSTGRES_TEST_DB=1` and optionally
    configure POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD,
    and POSTGRES_DB.
    """
    use_postgres = os.environ.get("USE_POSTGRES_TEST_DB") in ("1", "true", "True", "yes")
    if use_postgres:
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = os.environ.get("POSTGRES_PORT", "5433")
        user = os.environ.get("POSTGRES_USER", "aihr_user")
        password = os.environ.get("POSTGRES_PASSWORD", "aihr_dev_password_2025")
        db = os.environ.get("POSTGRES_DB", "aihr_test_db")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    # Default: SQLite in-memory
    return "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine(test_db_url):
    """Create test database engine.

    For SQLite we need `check_same_thread=False` and StaticPool to allow
    tests to share the same in-memory DB. For PostgreSQL we create a
    normal engine connected to the test Postgres instance.
    """
    if test_db_url.startswith("sqlite"):
        engine = create_engine(
            test_db_url,
            poolclass=StaticPool,  # Use static pool for testing
            connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
            echo=False  # Set to True for SQL debugging
        )
    else:
        # Real PostgreSQL - do not use StaticPool or check_same_thread
        engine = create_engine(test_db_url, echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============================================================================
# ASYNC TEST SUPPORT
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client(db_session) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async HTTP client for testing"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_organization(db_session):
    """Create sample organization for testing"""
    from app.models.organization import Organization
    from datetime import datetime
    
    org = Organization(
        name="Test Staffing Agency",
        slug="test-staffing",
        industry="Staffing",
        company_size="50-200",
        website="https://test-staffing.com",
        contact_email="contact@test-staffing.com",
        contact_phone="+1-555-0123",
        plan="professional",
        subscription_status="active",
        max_jobs=100,
        max_users=20,
        features={"multi_client": True, "ai_screening": True}
    )
    
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    
    return org


@pytest.fixture
def sample_candidate(db_session, sample_organization):
    """Create sample candidate for testing"""
    from app.models.candidate import Candidate, CandidateStatus
    
    candidate = Candidate(
        organization_id=sample_organization.id,
        full_name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-0100",
        location="New York, NY",
        current_role="Senior Software Engineer",
        total_experience_years=5,
        skills={"technical": ["Python", "FastAPI", "PostgreSQL", "React"], "soft": ["Communication"]},
        resume_text="Experienced software engineer with 5 years...",
        status=CandidateStatus.NEW,
        source="linkedin"
    )
    
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    
    return candidate



@pytest.fixture
def sample_job(db_session, sample_organization):
    """Create sample job for testing"""
    from app.models.job import Job, JobStatus, JobType, ExperienceLevel
    from datetime import datetime, timedelta
    
    job = Job(
        organization_id=sample_organization.id,
        title="Senior Python Developer",
        company_name="Test Staffing Agency",
        department="Engineering",
        location="New York, NY",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        description="We are looking for a senior Python developer...",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["React", "Docker", "AWS"],
        salary_min=120000,
        salary_max=160000,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        closes_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    return job



@pytest.fixture
def sample_application(db_session, sample_candidate, sample_job):
    """Create sample application for testing"""
    from app.models.application import Application, ApplicationStatus
    
    application = Application(
        job_id=sample_job.id,
        candidate_id=sample_candidate.id,
        status=ApplicationStatus.APPLIED,
        source="direct"
    )
    
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    
    return application



@pytest.fixture
def sample_interview(db_session, sample_candidate, sample_job, sample_application, sample_organization):
    """Create sample interview for testing"""
    from app.models.interview import Interview, InterviewStatus, SessionState
    from datetime import datetime, timedelta
    
    interview = Interview(
        candidate_id=sample_candidate.id,
        job_id=sample_job.id,
        application_id=sample_application.id,
        organization_id=sample_organization.id,
        interview_type="voice",
        platform="twilio",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        duration_minutes=30,
        status=InterviewStatus.SCHEDULED.value,
        session_state=SessionState.SCHEDULED.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db_session.add(interview)
    db_session.commit()
    db_session.refresh(interview)
    
    return interview


@pytest.fixture
def sample_user(db_session, sample_organization):
    """Create sample user for testing"""
    from app.models.user import User, UserRole
    
    user = User(
        organization_id=sample_organization.id,
        email="admin@test-staffing.com",
        hashed_password="$2b$12$dummy_hash",  # Dummy hash for testing
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def auth_headers(sample_user):
    """Mock authentication headers"""
    # TODO: Replace with actual JWT token when auth is implemented
    return {
        "Authorization": f"Bearer mock_token_user_{sample_user.id}",
        "X-Organization-ID": str(sample_user.organization_id)
    }


@pytest.fixture
def api_base_url():
    """API base URL for tests"""
    return "/api/v1"


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "playwright: marks tests requiring Playwright"
    )


# ============================================================================
# TEST DATABASE HELPERS
# ============================================================================

@pytest.fixture
def db_cleanup(db_session):
    """Cleanup database after test"""
    yield
    
    # Clear all tables
    from app.models.interview import Interview
    from app.models.application import Application
    from app.models.candidate import Candidate
    from app.models.job import Job
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.audit_log import AuditLog
    
    db_session.query(Interview).delete()
    db_session.query(Application).delete()
    db_session.query(Candidate).delete()
    db_session.query(Job).delete()
    db_session.query(User).delete()
    db_session.query(AuditLog).delete()
    db_session.query(Organization).delete()
    db_session.commit()
