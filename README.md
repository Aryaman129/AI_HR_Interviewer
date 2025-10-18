# 🤖 AI HR Interviewer

A fully local, AI-powered HR assistant system for automated candidate screening, voice interviews, and performance evaluation. Built to run completely offline on Windows 11 with no internet dependency.

> **Latest Update (October 2025)**: Repository cleaned and restructured for production use. All experimental files archived, dependencies updated with tf-keras fix, and proper .gitignore added.

## 🌟 Features

### Core Capabilities
- **Resume Filtering**: Automatically scan and rank resumes based on job requirements
- **Voice Interviews**: Conduct realistic AI interviews with speech-to-text and text-to-speech
- **Adaptive Questioning**: Dynamic interview flow based on candidate responses
- **Performance Evaluation**: Comprehensive scoring and recommendation system
- **Human-in-the-Loop**: Easy handoff to human recruiters when needed

### Interview Features
- Core HR questions (CTC expectations, job change reasons, location suitability)
- Resume verification questions with cross-checking
- Role-specific technical questions
- Intelligent follow-up questions based on response quality
- Real-time conversation logging and audio recording

### Technical Features
- **Fully Local**: No internet required, all processing on-device
- **Multi-format Support**: PDF, DOCX, TXT resume processing
- **Real-time Processing**: Live speech recognition and response generation
- **Comprehensive Logging**: Full conversation and audio logs
- **Analytics Dashboard**: Performance metrics and candidate insights

## 🏗️ Architecture

```
AI_HR_Interviewer/
├── backend/
│   ├── data/
│   │   ├── resumes/          # Uploaded resume files
│   │   └── vectorstore/      # Embeddings and search indices
│   └── logic/
│       ├── resume_filter.py  # Resume processing and ranking
│       └── interview_engine.py # Interview conductor
├── frontend/
│   ├── streamlit_app/
│   │   └── app.py            # Main web interface
│   ├── audio_logs/           # Interview audio recordings
│   └── chat_logs/            # Conversation transcripts
├── config/
│   ├── app_config.json       # Application configuration
│   ├── interview_questions.json # Interview templates
│   └── sample_jobs.json      # Sample job requirements
├── utils/
│   └── resume_collector.py   # Utility for collecting resumes
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── setup.py                  # Setup script
├── README.md                 # This file
├── DEMO_GUIDE.md             # Demo usage guide
└── VOICE_AI_GUIDE.md         # Voice AI features guide
```

## 🛠️ Technology Stack

### AI Models (Local)
- **LLM**: Ollama with Llama 3.1 or Mistral
- **Speech-to-Text**: OpenAI Whisper (local)
- **Text-to-Speech**: Coqui TTS
- **Embeddings**: Sentence Transformers

### Application Framework
- **Backend**: Python with FastAPI
- **Frontend**: Streamlit
- **Database**: SQLite + ChromaDB
- **Audio Processing**: SoundDevice, PyAudio

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 11
- **RAM**: 16 GB (recommended)
- **Storage**: 10 GB free space
- **GPU**: RTX 4050 or better (optional, for faster processing)

### Software Dependencies
- Python 3.10+
- Ollama (for local LLM)
- Git

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-username/AI_HR_Interviewer.git
cd AI_HR_Interviewer
```

### 2. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows

# Install requirements
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 3. Setup Ollama (Local LLM)
```bash
# Download and install Ollama from https://ollama.ai
# Then pull the required model
ollama pull llama3:latest

# Start Ollama server
ollama serve
```

### 4. Initialize Project
```bash
# Run setup to create directories and download models
python setup.py
```

### 5. Launch Application
```bash
streamlit run frontend/streamlit_app/app.py
```

### 6. Access Dashboard
Open your browser to `http://localhost:8501`

## 📖 Usage Guide

### Setting Up Job Requirements
1. Navigate to "Job Requirements" page
2. Either select a sample job or create custom requirements
3. Specify required/preferred skills, experience level, education
4. Save the requirements

### Processing Resumes
1. Go to "Resume Management" page
2. Upload resume files (PDF, DOCX, TXT)
3. Return to "Job Requirements" and click "Filter Resumes"
4. View ranked candidates on the Dashboard

### Conducting Interviews
1. Navigate to "Interview Conductor"
2. Select a candidate from the filtered list
3. Click "Start Interview" to begin
4. Follow the AI-guided interview process
5. Review results in the Analytics section

### Sample Data
The system includes sample resumes and job requirements for demonstration:
- 5 diverse resume profiles (Software Engineer, Cybersecurity, Data Scientist, etc.)
- 3 sample job requirements with different skill sets
- Pre-configured interview questions and scoring criteria

## 🎯 Interview Process

### Core Questions
1. **CTC Expectations**: "What is your expected CTC (Cost to Company)?"
2. **Job Change Reason**: "What is your reason for job change?"
3. **Location Suitability**: "Are you suitable to work at this location?"

### Adaptive Features
- **Resume Verification**: AI asks specific questions about claimed experience
- **Follow-up Questions**: Deeper probing based on response quality
- **Role-specific Questions**: Technical questions tailored to the job role
- **Dynamic Flow**: Interview adapts based on candidate responses

### Scoring System
- **Technical Skills**: 40% weight
- **Communication**: 30% weight  
- **Experience Match**: 30% weight
- **Pass Threshold**: 65% overall score

## 🔧 Configuration

### Model Configuration (`config/app_config.json`)
```json
{
  "models": {
    "llm": {
      "model_name": "llama3:latest",
      "temperature": 0.7
    },
    "whisper": {
      "model_size": "base"
    }
  }
}
```

### Interview Questions (`config/interview_questions.json`)
- Core questions for all interviews
- Role-specific question templates
- Follow-up question patterns
- Resume verification templates

## 📊 Analytics & Reporting

### Dashboard Metrics
- Total resumes processed
- Candidates filtered and ranked
- Interviews completed
- Score distributions

### Interview Analytics
- Response quality analysis
- Communication assessment
- Technical competency evaluation
- Recommendation generation

### Export Options
- JSON conversation logs
- Audio recordings
- Candidate scorecards
- Summary reports

## 🔒 Privacy & Security

- **Fully Local**: No data leaves your machine
- **No Internet Required**: Complete offline operation
- **Secure Storage**: Local file system storage
- **Data Control**: Full control over all candidate data

## 🛠️ Troubleshooting

### Common Issues

**Ollama Connection Error**
```bash
# Start Ollama service
ollama serve

# Verify models are available
ollama list
```

**Import Errors**
```bash
# Install dependencies
pip install -r requirements.txt

# Run from project root
cd AI_HR_Interviewer
streamlit run frontend/streamlit_app/app.py
```

**Audio Issues**
- Ensure microphone permissions are granted
- Check audio device settings in Windows
- Verify PyAudio installation

### Performance Optimization
- Use GPU acceleration for faster processing
- Adjust model sizes based on available RAM
- Configure batch processing for multiple resumes

## � Project Structure

The repository has been cleaned and organized for production use. All experimental and duplicate files have been moved to `old_experimental_files/` folder for reference.

### Core Files
- `frontend/streamlit_app/app.py` - Main application
- `backend/logic/resume_filter.py` - Resume processing
- `backend/logic/interview_engine.py` - Interview logic
- `utils/resume_collector.py` - Resume utilities
- `setup.py` - Project initialization

### Configuration
All configuration is in the `config/` directory:
- `app_config.json` - Model and path settings
- `interview_questions.json` - Question templates
- `sample_jobs.json` - Sample job requirements

## �🔮 Future Enhancements

### Planned Features
- **Real Phone Integration**: Connect to actual phone systems
- **Advanced Analytics**: ML-powered insights and predictions
- **Multi-language Support**: Interviews in multiple languages
- **Video Interviews**: Computer vision for non-verbal analysis
- **ATS Integration**: Connect to existing HR systems

### Extensibility
- Plugin architecture for custom interview modules
- API endpoints for external integrations
- Custom scoring algorithms
- Industry-specific question sets

## 📄 License

This project is for demonstration purposes. Please ensure compliance with local privacy and employment laws when using for actual recruitment.

## 🤝 Contributing

This is a demo project. For production use, consider:
- Enhanced security measures
- Scalability improvements
- Professional UI/UX design
- Comprehensive testing
- Legal compliance features

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review configuration files
3. Verify all dependencies are installed
4. Ensure Ollama is running properly

---

**Built with ❤️ for local AI-powered recruitment**
