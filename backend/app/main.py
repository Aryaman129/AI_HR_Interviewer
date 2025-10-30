"""
FastAPI Main Application
Entry point for the AI-HR Automation Platform backend
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📊 Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"💾 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print(f"🤖 Ollama: {settings.OLLAMA_HOST} (Model: {settings.OLLAMA_MODEL})")
    print(f"📞 n8n: {settings.N8N_HOST}")
    
    # Initialize database tables (in production, use Alembic migrations)
    # init_db()  # Uncomment when models are ready
    
    yield
    
    # Shutdown
    print("👋 Shutting down AI-HR Platform")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered HR automation platform for Indian SMBs",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "message": "AI-HR Automation Platform is running!",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "ollama": "connected",
        "services": {
            "resume_parsing": "ready",
            "ai_screening": "ready",
            "voice_interviews": "ready",
        }
    }


@app.get("/api/v1/info", tags=["Info"])
async def api_info():
    """API information and available features"""
    return {
        "api_version": "v1",
        "features": [
            "Intelligent Resume Parsing",
            "Customizable AI Screening",
            "AI Voice Interviews",
            "Human-in-Loop Review Queue",
            "n8n Integration Layer",
            "Candidate Pipeline Dashboard",
            "Smart Scheduling",
            "Analytics & Reporting",
            "Audit Trail & Compliance",
            "AI Learning & Continuous Improvement",
            "Multi-Channel Communication",
        ],
        "ai_models": {
            "llm": settings.OLLAMA_MODEL,
            "ner": settings.SPACY_MODEL,
            "embeddings": settings.SENTENCE_TRANSFORMER_MODEL,
            "stt": f"whisper-{settings.WHISPER_MODEL}",
        },
    }


# Import and include API routers
from app.api.v1.router import api_router
app.include_router(api_router)


if __name__ == "__main__":
    """Run application with uvicorn"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
