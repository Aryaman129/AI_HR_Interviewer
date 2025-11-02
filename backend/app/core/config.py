"""
Application Configuration
Manages all settings using Pydantic Settings for type safety and validation
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "AI-HR Automation Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    POSTGRES_USER: str = "aihr_user"
    POSTGRES_PASSWORD: str = "aihr_dev_password_2025"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "aihr_db"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set Celery URLs based on Redis
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
    
    # AI Services
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_API_KEY: Optional[str] = None  # For Ollama Cloud (set in environment, do NOT commit secrets)
    # Ollama Cloud host (used when OLLAMA_API_KEY is provided). Examples: https://ollama.com
    OLLAMA_CLOUD_URL: str = "https://ollama.com"
    
    # Google Gemini (Fallback LLM)
    GOOGLE_API_KEY: Optional[str] = None  # For Gemini API
    GEMINI_MODEL: str = "gemini-2.5-flash"  # gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash
    
    SPACY_MODEL: str = "en_core_web_lg"
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Toggle whether to use the LLM-based resume parser (when True) or the local spaCy parser
    USE_LLM_RESUME_PARSER: bool = True
    WHISPER_MODEL: str = "base"  # base, small, medium, large
    
    # Storage (Cloudflare R2)
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: str = "aihr-storage"
    R2_ENDPOINT_URL: Optional[str] = None
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: str = "noreply@aihr.local"
    
    # n8n
    N8N_HOST: str = "http://localhost:5678"
    N8N_API_KEY: Optional[str] = None
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    
    # CORS - parse as string from .env, split by comma
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
