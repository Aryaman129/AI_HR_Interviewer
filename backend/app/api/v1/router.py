"""
API v1 Router
Aggregates all v1 endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import resumes
from app.api.v1.endpoints import jobs
from app.api.v1.endpoints import screening

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(screening.router)

# Future endpoints (uncomment as you create them)
# api_router.include_router(candidates.router)
# api_router.include_router(applications.router)
# api_router.include_router(interviews.router)
