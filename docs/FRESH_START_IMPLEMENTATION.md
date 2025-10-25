# 🚀 AI-HR Platform v2.0 - FRESH START IMPLEMENTATION

**Date Started**: October 24, 2025  
**Timeline**: 8 Weeks (Full-time Development)  
**Approach**: Local-first, Zero-cost MVP, All 11 Features

---

## ✅ ENVIRONMENT AUDIT (Completed)

### What You Already Have:
```
✅ Docker 28.0.4 (installed)
✅ NVIDIA RTX 4050 6GB (6141 MiB VRAM, CUDA 13.0)
✅ Ollama 0.12.6 (installed, no models yet)
✅ Python packages (in ai_hr_advanced_2025 venv):
   - fastapi 0.115.9
   - sqlalchemy 1.4.54
   - sentence-transformers 4.0.1
   - langchain 0.3.21 + ollama integration
   - uvicorn 0.34.0
   - pydantic 2.10.6
   - spacy 3.8.7
   - torch 2.6.0
   - transformers 4.52.4
   - streamlit 1.45.1
```

### What's Missing (Need to Install):
```
❌ Whisper (openai-whisper)
❌ Twilio SDK (twilio)
❌ Redis client (redis)
❌ PostgreSQL adapter (psycopg2-binary)
❌ Celery (celery + kombu + amqp)
❌ Alembic (alembic)
❌ Additional: python-multipart, python-jose[cryptography]
❌ Docker Desktop NOT RUNNING (need to start)
❌ Llama 3.1 8B model (need to pull via Ollama)
❌ spaCy en_core_web_lg model (need to download)
```

---

## 📋 IMMEDIATE ACTION PLAN (Next 30 Minutes)

### Step 1: Start Docker Desktop
```powershell
# Start Docker Desktop from Start Menu or:
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
# Wait 2-3 minutes for Docker to fully start
# Verify: docker ps (should not show error)
```

### Step 2: Install Missing Python Packages
```powershell
cd D:\AiHr
.\ai_hr_advanced_2025\Scripts\activate

# Install missing packages
pip install openai-whisper twilio redis psycopg2-binary celery alembic python-multipart "python-jose[cryptography]" PyPDF2 python-docx

# Verify installations
pip list | Select-String "whisper|twilio|redis|psycopg2|celery|alembic"
```

### Step 3: Download AI Models
```powershell
# Download spaCy English model (500MB)
python -m spacy download en_core_web_lg

# Pull Llama 3.1 8B model via Ollama (4.7GB download)
& "C:\Users\Lenovo\AppData\Local\Programs\Ollama\ollama.exe" pull llama3.1:8b

# Verify models
python -m spacy info en_core_web_lg
& "C:\Users\Lenovo\AppData\Local\Programs\Ollama\ollama.exe" list
```

### Step 4: Archive Old Code & Create Fresh Structure
```powershell
# Create backup
cd D:\AiHr
New-Item -ItemType Directory -Path "old_workspace_backup" -Force
Move-Item -Path "backend", "frontend", "utils" -Destination "old_workspace_backup\" -Force -ErrorAction SilentlyContinue

# Create new project structure
New-Item -ItemType Directory -Path "backend/app/api/v1/endpoints" -Force
New-Item -ItemType Directory -Path "backend/app/core" -Force
New-Item -ItemType Directory -Path "backend/app/models" -Force
New-Item -ItemType Directory -Path "backend/app/services" -Force
New-Item -ItemType Directory -Path "backend/app/schemas" -Force
New-Item -ItemType Directory -Path "backend/alembic/versions" -Force
New-Item -ItemType Directory -Path "backend/tests" -Force
New-Item -ItemType Directory -Path "frontend/src/components" -Force
New-Item -ItemType Directory -Path "frontend/src/pages" -Force
New-Item -ItemType Directory -Path "frontend/src/hooks" -Force
New-Item -ItemType Directory -Path "frontend/src/services" -Force
New-Item -ItemType Directory -Path "frontend/src/utils" -Force
New-Item -ItemType Directory -Path "infra" -Force
New-Item -ItemType Directory -Path "docs" -Force
New-Item -ItemType Directory -Path "scripts" -Force
```

---

## 🐳 DOCKER INFRASTRUCTURE SETUP

Create `infra/docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    container_name: aihr_postgres
    environment:
      POSTGRES_USER: aihr_user
      POSTGRES_PASSWORD: aihr_local_dev_2025
      POSTGRES_DB: aihr_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - aihr_network

  redis:
    image: redis:7-alpine
    container_name: aihr_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - aihr_network

  n8n:
    image: n8nio/n8n:latest
    container_name: aihr_n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=aihr2025
      - WEBHOOK_URL=http://localhost:5678/
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres
      - redis
    networks:
      - aihr_network

volumes:
  postgres_data:
  redis_data:
  n8n_data:

networks:
  aihr_network:
    driver: bridge
```

**Start Infrastructure**:
```powershell
cd D:\AiHr\infra
docker-compose up -d

# Verify all containers running
docker ps

# Expected output: 3 containers (postgres, redis, n8n)
```

---

## 🔧 BACKEND FASTAPI SETUP (Week 1)

### Create `backend/app/core/config.py`:
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-HR Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "aihr_user"
    POSTGRES_PASSWORD: str = "aihr_local_dev_2025"
    POSTGRES_DB: str = "aihr_platform"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # Twilio (add your credentials later)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        case_sensitive = True

settings = Settings()

# Build Database URI
if not settings.SQLALCHEMY_DATABASE_URI:
    settings.SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
    )
```

### Create `backend/app/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Create `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "AI-HR Platform API v2.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Create `backend/app/api/v1/api.py`:
```python
from fastapi import APIRouter
# from app.api.v1.endpoints import resumes, candidates, interviews, auth

api_router = APIRouter()

# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
# api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
# api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working!"}
```

### Create `backend/requirements.txt`:
```txt
fastapi==0.115.9
uvicorn[standard]==0.34.0
sqlalchemy==1.4.54
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.10.6
pydantic-settings==2.8.1
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
celery==5.4.0
redis==5.0.1
langchain==0.3.21
langchain-ollama==0.3.0
sentence-transformers==4.0.1
spacy==3.8.7
openai-whisper==20240930
twilio==9.3.9
PyPDF2==3.0.1
python-docx==1.1.2
boto3==1.35.0  # For Cloudflare R2 (S3-compatible)
```

**Start Backend**:
```powershell
cd D:\AiHr\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access: http://localhost:8000/docs
```

---

## ⚛️ FRONTEND REACT SETUP (Week 1)

### Initialize React Project with Vite:
```powershell
cd D:\AiHr\frontend

# Create Vite project
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Install additional libraries
npm install @ant-design/icons antd axios react-router-dom @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Configure Tailwind CSS (`frontend/tailwind.config.js`):
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### Update `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Start Frontend**:
```powershell
cd D:\AiHr\frontend
npm run dev

# Access: http://localhost:5173
```

---

## 📅 8-WEEK TIMELINE (Detailed)

### **Week 1: Foundation (Oct 24-30)**
- [x] Environment audit
- [ ] Docker infrastructure running
- [ ] Backend FastAPI skeleton
- [ ] Frontend React skeleton
- [ ] Database models design
- [ ] Authentication system

### **Week 2: AI Services (Oct 31 - Nov 6)**
- [ ] Ollama integration tested
- [ ] Whisper STT integration
- [ ] spaCy NER pipeline
- [ ] sentence-transformers embeddings
- [ ] Celery task queue setup

### **Week 3: Features 1-2 (Nov 7-13)**
- [ ] Resume parsing API (PDF/DOCX/TXT)
- [ ] Resume upload UI
- [ ] AI screening engine
- [ ] Screening templates CRUD
- [ ] Candidate scoring dashboard

### **Week 4: Feature 3 (Nov 14-20)**
- [ ] Twilio Voice integration
- [ ] Interview flow engine
- [ ] Real-time transcription
- [ ] Recording storage (Cloudflare R2)
- [ ] Interview UI

### **Week 5: Feature 6 (Nov 21-27)**
- [ ] n8n workflows setup
- [ ] Job board integrations
- [ ] Email parsing automation
- [ ] WhatsApp notifications
- [ ] Webhook handlers

### **Week 6: Features 5, 7 (Nov 28 - Dec 4)**
- [ ] Human review queue
- [ ] Kanban board UI
- [ ] Feedback loop system
- [ ] Pipeline dashboard
- [ ] Real-time updates (WebSockets)

### **Week 7: Features 8, 9, 12 (Dec 5-11)**
- [ ] Google Calendar integration
- [ ] Smart scheduling logic
- [ ] Analytics dashboard
- [ ] Multi-channel communication
- [ ] Template system

### **Week 8: Features 10, 11 + Launch (Dec 12-18)**
- [ ] GDPR compliance features
- [ ] Audit trail system
- [ ] AI feedback loop
- [ ] Testing suite
- [ ] Production deployment
- [ ] Documentation

---

## 🎯 IMMEDIATE NEXT STEPS (TODAY)

1. **Start Docker Desktop** (2 mins)
2. **Install missing packages** (5 mins)
3. **Download AI models** (15-20 mins - large downloads)
4. **Start Docker containers** (2 mins)
5. **Create backend structure** (5 mins)
6. **Test FastAPI** (3 mins)
7. **Initialize React frontend** (5 mins)

**Total Time**: ~40 minutes to have a working foundation!

---

## 🔑 KEY DECISIONS

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Database** | PostgreSQL (local Docker) | pgvector for embeddings, free, performant |
| **Cache/Queue** | Redis (local Docker) | Celery backend, session storage |
| **LLM** | Llama 3.1 8B (Ollama) | Runs on RTX 4050, zero API costs |
| **STT** | Whisper base/small | Local GPU inference, accurate |
| **Deployment (later)** | TBD (Heroku vs DO) | Decide after local testing |
| **Frontend** | Vite + React 18 | Fast HMR, modern tooling |

---

## 📊 SUCCESS METRICS

- [ ] All Docker containers healthy
- [ ] FastAPI docs accessible at localhost:8000/docs
- [ ] React app running at localhost:5173
- [ ] Ollama responds to Llama 3.1 8B queries
- [ ] PostgreSQL + pgvector extension working
- [ ] spaCy en_core_web_lg loaded
- [ ] Redis connection successful

---

**Ready to start?** Let's execute Step 1! 🚀
