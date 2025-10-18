# AI HR Interviewer - Project Structure Documentation

**Last Updated**: October 18, 2025

## 📋 Overview

This document describes the clean, production-ready structure of the AI HR Interviewer project after the October 2025 cleanup and reorganization.

## 🗂️ Directory Structure

```
AI_HR_Interviewer/
├── backend/
│   ├── data/
│   │   ├── resumes/          # Upload candidate resumes here (PDF, DOCX, TXT)
│   │   └── vectorstore/      # Auto-generated embeddings (git-ignored)
│   └── logic/
│       ├── resume_filter.py  # Resume parsing and filtering logic
│       └── interview_engine.py # AI interview conductor
│
├── frontend/
│   ├── streamlit_app/
│   │   └── app.py            # Main Streamlit web application
│   ├── audio_logs/           # Voice interview recordings (git-ignored)
│   └── chat_logs/            # Text conversation logs (git-ignored)
│
├── config/
│   ├── app_config.json       # Main configuration (models, paths, scoring)
│   ├── interview_questions.json # Interview question templates
│   └── sample_jobs.json      # Sample job requirement templates
│
├── utils/
│   └── resume_collector.py   # Utilities for resume collection and processing
│
├── old_experimental_files/   # Archived experimental code (not for production)
│
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python package dependencies
├── setup.py                  # Project initialization script
├── README.md                 # Main documentation
├── DEMO_GUIDE.md             # Step-by-step demo guide
└── VOICE_AI_GUIDE.md         # Voice AI features documentation
```

## 📄 Key Files Description

### Backend Components

#### `backend/logic/resume_filter.py`
**Purpose**: Resume processing and candidate filtering
- Extracts text from PDF, DOCX, and TXT files
- Parses structured information (skills, experience, education)
- Generates embeddings for semantic search
- Ranks candidates based on job requirements
- Key Classes: `ResumeFilter`

#### `backend/logic/interview_engine.py`
**Purpose**: AI-powered interview conductor
- Manages interview sessions
- Integrates Whisper (speech-to-text) and TTS (text-to-speech)
- Connects to Ollama for LLM responses
- Handles interview flow and question sequencing
- Saves audio and text logs
- Key Classes: `InterviewEngine`

### Frontend Components

#### `frontend/streamlit_app/app.py`
**Purpose**: Main web interface
- Dashboard with candidate overview
- Resume upload and management
- Job requirements configuration
- Interview conductor interface
- Analytics and reporting
- Uses Streamlit for UI

### Configuration Files

#### `config/app_config.json`
Main application configuration:
- Model settings (Ollama, Whisper, TTS, embeddings)
- Interview parameters (duration, thresholds)
- Scoring weights
- File paths

#### `config/interview_questions.json`
Interview question templates:
- Core HR questions
- Role-specific technical questions
- Follow-up question patterns
- Resume verification templates

#### `config/sample_jobs.json`
Sample job requirement templates for testing

### Utility Scripts

#### `utils/resume_collector.py`
Utilities for:
- Generating sample resumes
- Creating job requirement templates
- Bulk resume processing

#### `setup.py`
Project initialization script:
- Creates directory structure
- Installs Python dependencies
- Downloads AI models (via Ollama)
- Generates sample data

## 🔧 Configuration Details

### Environment Setup

1. **Virtual Environment**: Create isolated Python environment
2. **Dependencies**: Install from `requirements.txt`
3. **Models**: Download via Ollama and setup script
4. **Configuration**: Customize `config/app_config.json`

### Model Configuration

The system uses these AI models:
- **LLM**: Ollama with Llama 3 (configurable)
- **Speech-to-Text**: OpenAI Whisper (base model)
- **Text-to-Speech**: Coqui TTS (Tacotron2-DDC)
- **Embeddings**: all-MiniLM-L6-v2 (Sentence Transformers)

### Path Configuration

All paths are relative to project root:
- Resumes: `backend/data/resumes/`
- Vector store: `backend/data/vectorstore/`
- Audio logs: `frontend/audio_logs/`
- Chat logs: `frontend/chat_logs/`

## 🚫 Excluded from Git

The following are automatically excluded (see `.gitignore`):
- Virtual environments (`venv/`, `ai_hr_*/`)
- Python cache (`__pycache__/`, `*.pyc`)
- Model files (`backend/models/`)
- Vector stores (`backend/data/vectorstore/`)
- Uploaded resumes (`backend/data/resumes/*.pdf`, etc.)
- Audio logs (`frontend/audio_logs/*.wav`)
- Chat logs (`frontend/chat_logs/*.json`)
- IDE files (`.vscode/`, `.idea/`)

## 📦 Dependencies

Key Python packages (see `requirements.txt` for complete list):
- **Framework**: streamlit>=1.32.0
- **AI/ML**: transformers>=4.38.0, torch>=2.2.0, sentence-transformers>=2.2.2
- **Speech**: openai-whisper, TTS>=0.22.0, pyttsx3
- **LLM**: ollama>=0.1.7, langchain>=0.1.0
- **Document Processing**: PyPDF2, pdfplumber, python-docx
- **Vector DB**: chromadb>=0.4.22, faiss-cpu>=1.7.4

## 🗄️ Archived Files

The `old_experimental_files/` directory contains:
- Previous iterations of the main application
- Experimental voice interview implementations
- Multiple demo applications
- Old requirement files

These files are kept for reference but should NOT be used in production.

## 🔄 Workflow

### Resume Processing Workflow
1. Upload resumes to `backend/data/resumes/`
2. Run resume filter through web UI
3. System generates embeddings in `backend/data/vectorstore/`
4. Candidates ranked and displayed on dashboard

### Interview Workflow
1. Select candidate from filtered list
2. Start interview session
3. AI asks questions using TTS
4. Candidate responds (captured via Whisper STT)
5. LLM generates intelligent follow-ups
6. Session logged to audio_logs/ and chat_logs/
7. Final scoring and recommendations

## 📊 Data Flow

```
Resume Upload
    ↓
Resume Filter (parsing, embedding)
    ↓
Vector Store (semantic search)
    ↓
Candidate Ranking
    ↓
Interview Setup
    ↓
Interview Engine (STT ↔ LLM ↔ TTS)
    ↓
Logging & Scoring
    ↓
Analytics Dashboard
```

## 🔐 Security Considerations

- All processing is local (no internet required)
- No data sent to external services
- Candidate data stored locally
- Secure file handling for resume uploads
- Audio logs can be encrypted (future enhancement)

## 🛠️ Development Guidelines

### Adding New Features
1. Backend logic goes in `backend/logic/`
2. UI components in `frontend/streamlit_app/`
3. Configuration in `config/*.json`
4. Update this document with changes

### Testing
- Test resume processing with various formats
- Verify interview flow with different scenarios
- Check audio recording and playback
- Validate scoring logic

### Best Practices
- Keep experimental code out of main branches
- Update configuration files instead of hardcoding
- Log important events for debugging
- Follow existing code structure and naming conventions

## 📚 Additional Documentation

- `README.md` - Quick start and overview
- `DEMO_GUIDE.md` - Step-by-step demo walkthrough
- `VOICE_AI_GUIDE.md` - Voice AI features and setup

## 🔄 Version History

### v1.0.0 (October 2025)
- Clean project structure established
- Removed experimental files
- Updated dependencies (tf-keras fix)
- Added comprehensive .gitignore
- Documentation updates

## 🤝 Contributing

When contributing to this project:
1. Maintain the established directory structure
2. Update documentation for new features
3. Test thoroughly before committing
4. Keep experimental work in separate branches
5. Update requirements.txt if adding dependencies

## 📞 Support

For issues or questions:
1. Check README.md for common solutions
2. Review configuration files
3. Verify all dependencies are installed
4. Check Ollama is running for LLM features

---

**Note**: This is a production-ready structure. Keep it clean and well-organized for easy maintenance and collaboration.
