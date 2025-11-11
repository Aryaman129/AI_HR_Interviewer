"""
API v1 Router
Aggregates all v1 endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import resumes
from app.api.v1.endpoints import jobs
from app.api.v1.endpoints import screening
from app.api.v1.endpoints import knowledge
from app.api.v1.endpoints import applications
from app.api.v1.endpoints import interviews
from app.api.v1.endpoints import users

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(screening.router, prefix="/screening", tags=["Screening"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Future endpoints (uncomment as you create them)
# api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
