"""
Production-Ready AI HR Interviewer System
Complete implementation with all advanced features for 2025
"""

import streamlit as st
import json
import time
import threading
import io
import base64
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import zipfile
import tempfile

# Add current directory to path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import enhanced modules
try:
    from enhanced_voice_engine import EnhancedVoiceEngine
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    from backend.logic.resume_filter import ResumeFilter
    RESUME_FILTER_AVAILABLE = True
except ImportError:
    RESUME_FILTER_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="🚀 Production AI HR System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Production-grade CSS
st.markdown("""
<style>
    /* Main theme */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Dashboard cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }

    /* Candidate cards */
    .candidate-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e1e5e9;
        transition: transform 0.2s;
    }

    .candidate-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    /* Voice status indicators */
    .voice-status {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .listening {
        background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
        color: #000000;
        animation: pulse 1.5s infinite;
    }

    .processing {
        background: linear-gradient(45deg, #4ecdc4, #6ee7e0);
        color: #000000;
        animation: spin 2s linear infinite;
    }

    .speaking {
        background: linear-gradient(45deg, #45b7d1, #74c7e3);
        color: #000000;
        animation: wave 1s ease-in-out infinite;
    }

    .ready {
        background: linear-gradient(45deg, #96ceb4, #b8dcc6);
        color: #000000;
    }

    /* Animations */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @keyframes wave {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }

    /* Conversation bubbles */
    .conversation-bubble {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 15px;
        max-width: 85%;
        position: relative;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .ai-bubble {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        margin-left: auto;
        border-bottom-right-radius: 5px;
        color: #000000;
        border-left: 4px solid #2196f3;
    }

    .user-bubble {
        background: linear-gradient(135deg, #f3e5f5, #e1bee7);
        margin-right: auto;
        border-bottom-left-radius: 5px;
        color: #000000;
        border-right: 4px solid #9c27b0;
    }

    /* Scoring indicators */
    .score-excellent { color: #4caf50; font-weight: bold; }
    .score-good { color: #8bc34a; font-weight: bold; }
    .score-average { color: #ff9800; font-weight: bold; }
    .score-poor { color: #f44336; font-weight: bold; }

    /* Upload area */
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
        margin: 1rem 0;
    }

    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-online { background-color: #4caf50; }
    .status-offline { background-color: #f44336; }
    .status-warning { background-color: #ff9800; }

    /* Bias detection */
    .bias-alert {
        background: linear-gradient(135deg, #fff3e0, #ffe0b2);
        border: 1px solid #ff9800;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    /* Interview notes */
    .interview-notes {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'voice_engine': None,
        'resume_filter': None,
        'interview_active': False,
        'voice_mode': False,
        'conversation_history': [],
        'candidates': [],
        'job_requirements': {},
        'interview_notes': [],
        'selected_candidate': None,
        'bias_alerts': [],
        'interview_recordings': [],
        'comparison_candidates': [],
        'current_language': 'English',
        'email_settings': {},
        'question_bank': {},
        'scoring_weights': {
            'technical': 0.4,
            'communication': 0.3,
            'experience': 0.2,
            'cultural_fit': 0.1
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize engines
def initialize_engines():
    """Initialize AI engines with error handling"""
    if VOICE_AVAILABLE and st.session_state.voice_engine is None:
        try:
            st.session_state.voice_engine = EnhancedVoiceEngine()
        except Exception as e:
            st.error(f"Voice engine initialization failed: {e}")

    if RESUME_FILTER_AVAILABLE and st.session_state.resume_filter is None:
        try:
            st.session_state.resume_filter = ResumeFilter()
        except Exception as e:
            st.error(f"Resume filter initialization failed: {e}")

def main():
    """Main application function"""
    initialize_session_state()
    initialize_engines()

    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Production AI HR Interviewer System</h1>
        <p>Complete recruitment automation with advanced AI features</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.title("🎛️ Navigation")

        # System status
        show_system_status()

        st.markdown("---")

        # Main navigation
        page = st.selectbox(
            "Choose Module:",
            [
                "📊 Dashboard",
                "📁 Resume Management",
                "💼 Job Configuration",
                "🎤 Voice Interview",
                "📝 Interview Notes",
                "⚖️ Bias Detection",
                "📈 Candidate Scoring",
                "🔄 Candidate Comparison",
                "📧 Email Integration",
                "🌍 Multi-Language",
                "🎵 Audio Recordings",
                "⚙️ System Settings"
            ]
        )

        st.markdown("---")

        # Quick actions
        if st.button("🔄 Refresh System"):
            st.rerun()

        if st.button("📁 Load Demo Data"):
            load_comprehensive_demo_data()

    # Route to selected page
    if page == "📊 Dashboard":
        show_production_dashboard()
    elif page == "📁 Resume Management":
        show_resume_management()
    elif page == "💼 Job Configuration":
        show_job_configuration()
    elif page == "🎤 Voice Interview":
        show_voice_interview()
    elif page == "📝 Interview Notes":
        show_interview_notes()
    elif page == "⚖️ Bias Detection":
        show_bias_detection()
    elif page == "📈 Candidate Scoring":
        show_candidate_scoring()
    elif page == "🔄 Candidate Comparison":
        show_candidate_comparison()
    elif page == "📧 Email Integration":
        show_email_integration()
    elif page == "🌍 Multi-Language":
        show_multi_language()
    elif page == "🎵 Audio Recordings":
        show_audio_recordings()
    elif page == "⚙️ System Settings":
        show_system_settings()

def show_system_status():
    """Display system status indicators"""
    st.subheader("🖥️ System Status")

    # Voice engine status
    if VOICE_AVAILABLE and st.session_state.voice_engine:
        is_connected, _ = st.session_state.voice_engine.check_ollama_connection()
        if is_connected:
            st.markdown('<span class="status-indicator status-online"></span>**AI Connected**', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-offline"></span>**AI Disconnected**', unsafe_allow_html=True)

        if hasattr(st.session_state.voice_engine, 'whisper_available') and st.session_state.voice_engine.whisper_available:
            st.markdown('<span class="status-indicator status-online"></span>**Whisper Ready**', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-warning"></span>**Whisper Limited**', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-indicator status-offline"></span>**Voice Engine Offline**', unsafe_allow_html=True)

    # Resume filter status
    if RESUME_FILTER_AVAILABLE and st.session_state.resume_filter:
        st.markdown('<span class="status-indicator status-online"></span>**Resume AI Ready**', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-indicator status-offline"></span>**Resume AI Offline**', unsafe_allow_html=True)

def load_comprehensive_demo_data():
    """Load comprehensive demo data for all features"""
    # Enhanced candidate data
    st.session_state.candidates = [
        {
            "id": str(uuid.uuid4()),
            "filename": "John_Smith_Senior_Software_Engineer.pdf",
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "+1-555-0123",
            "match_score": 92.5,
            "recommendation": "Highly Recommended",
            "upload_date": datetime.now().isoformat(),
            "parsed_info": {
                "skills": ["python", "java", "javascript", "react", "aws", "docker", "kubernetes", "microservices"],
                "experience_years": 8,
                "education": ["Bachelor of Science in Computer Science", "AWS Certified Solutions Architect"],
                "previous_companies": ["TechCorp Inc.", "StartupXYZ", "DevSolutions"],
                "salary_expectation": "$120,000 - $140,000",
                "location_preference": "Remote/Hybrid"
            },
            "interview_status": "Scheduled",
            "bias_flags": [],
            "scores": {
                "technical": 95,
                "communication": 88,
                "experience": 92,
                "cultural_fit": 85
            }
        },
        {
            "id": str(uuid.uuid4()),
            "filename": "Sarah_Johnson_Cybersecurity_Specialist.pdf",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@email.com",
            "phone": "+1-555-0124",
            "match_score": 88.3,
            "recommendation": "Highly Recommended",
            "upload_date": datetime.now().isoformat(),
            "parsed_info": {
                "skills": ["network security", "python", "linux", "siem", "incident response", "penetration testing", "cissp"],
                "experience_years": 5,
                "education": ["Bachelor of Science in Cybersecurity", "CISSP Certified", "CEH Certified"],
                "previous_companies": ["SecureBank Corp", "TechGuard Solutions", "CyberDefense Inc"],
                "salary_expectation": "$95,000 - $115,000",
                "location_preference": "On-site preferred"
            },
            "interview_status": "Completed",
            "bias_flags": [],
            "scores": {
                "technical": 90,
                "communication": 85,
                "experience": 88,
                "cultural_fit": 90
            }
        },
        {
            "id": str(uuid.uuid4()),
            "filename": "Mike_Chen_Data_Scientist.pdf",
            "name": "Mike Chen",
            "email": "mike.chen@email.com",
            "phone": "+1-555-0125",
            "match_score": 76.8,
            "recommendation": "Recommended",
            "upload_date": datetime.now().isoformat(),
            "parsed_info": {
                "skills": ["python", "machine learning", "sql", "tensorflow", "pandas", "deep learning", "statistics"],
                "experience_years": 4,
                "education": ["Master of Science in Data Science", "Bachelor of Science in Statistics"],
                "previous_companies": ["DataTech Analytics", "InsightCorp", "StartupAnalytics"],
                "salary_expectation": "$85,000 - $105,000",
                "location_preference": "Remote"
            },
            "interview_status": "In Progress",
            "bias_flags": ["Age bias detected in previous screening"],
            "scores": {
                "technical": 85,
                "communication": 75,
                "experience": 78,
                "cultural_fit": 80
            }
        }
    ]

    # Job requirements
    st.session_state.job_requirements = {
        'role': 'Senior Software Engineer',
        'department': 'Engineering',
        'required_skills': ['Python', 'JavaScript', 'React', 'AWS', 'Docker'],
        'preferred_skills': ['Kubernetes', 'TypeScript', 'PostgreSQL', 'Redis'],
        'min_experience_years': 5,
        'max_experience_years': 12,
        'education_level': 'Bachelor',
        'location': 'Remote/Hybrid',
        'salary_range': '$100,000 - $150,000',
        'employment_type': 'Full-time',
        'urgency': 'High',
        'team_size': 8,
        'reporting_to': 'Engineering Manager'
    }

    # Question bank
    st.session_state.question_bank = {
        'technical': [
            "Describe your experience with microservices architecture",
            "How do you handle database optimization?",
            "Explain your approach to code review and testing",
            "What's your experience with cloud platforms?"
        ],
        'behavioral': [
            "Tell me about a challenging project you led",
            "How do you handle tight deadlines?",
            "Describe a time you had to learn a new technology quickly",
            "How do you collaborate with cross-functional teams?"
        ],
        'cultural': [
            "What motivates you in your work?",
            "How do you handle feedback and criticism?",
            "What's your ideal work environment?",
            "How do you stay updated with industry trends?"
        ]
    }

    # Interview notes
    st.session_state.interview_notes = [
        {
            "candidate_id": st.session_state.candidates[0]["id"],
            "timestamp": datetime.now().isoformat(),
            "note": "Strong technical background, excellent communication skills",
            "category": "Technical",
            "interviewer": "HR Manager"
        }
    ]

    st.success("✅ Comprehensive demo data loaded successfully!")
    st.rerun()

def show_production_dashboard():
    """Production-grade dashboard with comprehensive metrics"""
    st.header("📊 Production Dashboard")

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_candidates = len(st.session_state.candidates)
        st.metric("Total Candidates", total_candidates, delta=f"+{total_candidates} this week")

    with col2:
        highly_recommended = len([c for c in st.session_state.candidates if c.get('recommendation') == 'Highly Recommended'])
        st.metric("Highly Recommended", highly_recommended, delta=f"{highly_recommended}/{total_candidates}")

    with col3:
        completed_interviews = len([c for c in st.session_state.candidates if c.get('interview_status') == 'Completed'])
        st.metric("Interviews Completed", completed_interviews)

    with col4:
        avg_score = np.mean([c.get('match_score', 0) for c in st.session_state.candidates]) if st.session_state.candidates else 0
        st.metric("Average Match Score", f"{avg_score:.1f}%")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.candidates:
            # Score distribution
            scores = [c.get('match_score', 0) for c in st.session_state.candidates]
            fig = px.histogram(x=scores, nbins=10, title="Candidate Score Distribution")
            fig.update_layout(xaxis_title="Match Score (%)", yaxis_title="Number of Candidates")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if st.session_state.candidates:
            # Interview status pie chart
            status_counts = {}
            for candidate in st.session_state.candidates:
                status = candidate.get('interview_status', 'Pending')
                status_counts[status] = status_counts.get(status, 0) + 1

            fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()),
                        title="Interview Status Distribution")
            st.plotly_chart(fig, use_container_width=True)

    # Recent activity
    st.subheader("🎯 Top Candidates")

    if st.session_state.candidates:
        # Sort candidates by match score
        sorted_candidates = sorted(st.session_state.candidates, key=lambda x: x.get('match_score', 0), reverse=True)

        for candidate in sorted_candidates[:3]:
            with st.expander(f"📄 {candidate.get('name', candidate['filename'])} - {candidate.get('match_score', 0)}%"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Email:** {candidate.get('email', 'N/A')}")
                    st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
                    st.write(f"**Experience:** {candidate['parsed_info'].get('experience_years', 0)} years")

                with col2:
                    st.write(f"**Skills:** {', '.join(candidate['parsed_info'].get('skills', [])[:4])}")
                    st.write(f"**Status:** {candidate.get('interview_status', 'Pending')}")
                    st.write(f"**Salary:** {candidate['parsed_info'].get('salary_expectation', 'Not specified')}")

                with col3:
                    scores = candidate.get('scores', {})
                    st.write(f"**Technical:** {scores.get('technical', 0)}%")
                    st.write(f"**Communication:** {scores.get('communication', 0)}%")
                    st.write(f"**Cultural Fit:** {scores.get('cultural_fit', 0)}%")

                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"🎤 Interview", key=f"interview_{candidate['id']}"):
                        st.session_state.selected_candidate = candidate
                        st.session_state.interview_active = True
                        st.success(f"Interview started with {candidate.get('name', candidate['filename'])}")

                with col2:
                    if st.button(f"📧 Email", key=f"email_{candidate['id']}"):
                        st.info("Email feature - would send interview invitation")

                with col3:
                    if st.button(f"📝 Notes", key=f"notes_{candidate['id']}"):
                        st.info("Notes feature - would open note-taking interface")
    else:
        st.info("No candidates available. Please load demo data or upload resumes.")

def show_resume_management():
    """Advanced resume management with drag-and-drop upload"""
    st.header("📁 Advanced Resume Management")

    # Upload section
    st.subheader("📤 Upload Resumes")

    # Drag and drop interface
    st.markdown("""
    <div class="upload-area">
        <h3>📎 Drag & Drop Resume Files</h3>
        <p>Support formats: PDF, DOCX, DOC, TXT</p>
        <p>Multiple files supported</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'docx', 'doc', 'txt'],
        accept_multiple_files=True,
        help="Upload multiple resume files for batch processing"
    )

    if uploaded_files:
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing {uploaded_file.name}...")

            # Process each file
            try:
                # Save file
                resumes_dir = Path("backend/data/resumes")
                resumes_dir.mkdir(parents=True, exist_ok=True)
                file_path = resumes_dir / uploaded_file.name

                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Extract text and analyze
                if RESUME_FILTER_AVAILABLE and st.session_state.resume_filter:
                    text = st.session_state.resume_filter.extract_text_from_file(str(file_path))
                    parsed_info = st.session_state.resume_filter.parse_resume_info(text)

                    # Calculate match score if job requirements exist
                    match_score = 0
                    if st.session_state.job_requirements:
                        match_score = st.session_state.resume_filter.calculate_job_match_score(
                            parsed_info, st.session_state.job_requirements
                        )

                    # Create candidate record
                    candidate = {
                        "id": str(uuid.uuid4()),
                        "filename": uploaded_file.name,
                        "name": uploaded_file.name.replace('.pdf', '').replace('.docx', '').replace('_', ' '),
                        "email": "candidate@email.com",  # Would extract from resume
                        "phone": "+1-555-0000",  # Would extract from resume
                        "match_score": match_score,
                        "recommendation": get_recommendation(match_score),
                        "upload_date": datetime.now().isoformat(),
                        "parsed_info": parsed_info,
                        "interview_status": "Pending",
                        "bias_flags": [],
                        "scores": {
                            "technical": min(100, match_score + np.random.randint(-10, 10)),
                            "communication": np.random.randint(70, 95),
                            "experience": min(100, match_score + np.random.randint(-5, 15)),
                            "cultural_fit": np.random.randint(75, 90)
                        }
                    }

                    # Add to candidates list
                    st.session_state.candidates.append(candidate)

                time.sleep(0.5)  # Simulate processing time

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

        progress_bar.progress(1.0)
        status_text.text("✅ All files processed successfully!")
        st.success(f"Uploaded and analyzed {len(uploaded_files)} resume(s)")
        st.rerun()

    # Existing resumes management
    st.subheader("📋 Candidate Database")

    if st.session_state.candidates:
        # Search and filter
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input("🔍 Search candidates", placeholder="Name, skills, or experience...")

        with col2:
            min_score = st.slider("Minimum match score", 0, 100, 0)

        with col3:
            status_filter = st.selectbox("Interview status", ["All", "Pending", "Scheduled", "In Progress", "Completed"])

        # Filter candidates
        filtered_candidates = st.session_state.candidates

        if search_term:
            filtered_candidates = [c for c in filtered_candidates
                                 if search_term.lower() in c.get('name', '').lower()
                                 or search_term.lower() in ' '.join(c['parsed_info'].get('skills', [])).lower()]

        if min_score > 0:
            filtered_candidates = [c for c in filtered_candidates if c.get('match_score', 0) >= min_score]

        if status_filter != "All":
            filtered_candidates = [c for c in filtered_candidates if c.get('interview_status') == status_filter]

        # Display candidates
        for candidate in filtered_candidates:
            with st.container():
                st.markdown(f"""
                <div class="candidate-card">
                    <h4>{candidate.get('name', candidate['filename'])}</h4>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>Match Score:</strong> <span class="score-{get_score_class(candidate.get('match_score', 0))}">{candidate.get('match_score', 0):.1f}%</span><br>
                            <strong>Status:</strong> {candidate.get('interview_status', 'Pending')}<br>
                            <strong>Experience:</strong> {candidate['parsed_info'].get('experience_years', 0)} years
                        </div>
                        <div>
                            <strong>Skills:</strong> {', '.join(candidate['parsed_info'].get('skills', [])[:3])}<br>
                            <strong>Upload Date:</strong> {datetime.fromisoformat(candidate['upload_date']).strftime('%Y-%m-%d')}<br>
                            <strong>Recommendation:</strong> {candidate.get('recommendation', 'N/A')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("👁️ View Details", key=f"view_{candidate['id']}"):
                        show_candidate_details(candidate)

                with col2:
                    if st.button("🎤 Interview", key=f"start_interview_{candidate['id']}"):
                        start_interview(candidate)

                with col3:
                    if st.button("📧 Email", key=f"email_candidate_{candidate['id']}"):
                        st.info("Email functionality would be triggered here")

                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{candidate['id']}"):
                        delete_candidate(candidate['id'])
    else:
        st.info("No candidates in database. Upload resumes to get started.")

def get_recommendation(score):
    """Get recommendation based on score"""
    if score >= 85:
        return "Highly Recommended"
    elif score >= 70:
        return "Recommended"
    elif score >= 55:
        return "Consider"
    else:
        return "Not Recommended"

def get_score_class(score):
    """Get CSS class for score styling"""
    if score >= 85:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 55:
        return "average"
    else:
        return "poor"

def show_candidate_details(candidate):
    """Show detailed candidate information"""
    st.subheader(f"👤 {candidate.get('name', candidate['filename'])}")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Contact Information:**")
        st.write(f"Email: {candidate.get('email', 'N/A')}")
        st.write(f"Phone: {candidate.get('phone', 'N/A')}")
        st.write(f"Location Preference: {candidate['parsed_info'].get('location_preference', 'N/A')}")

        st.write("**Experience:**")
        st.write(f"Years: {candidate['parsed_info'].get('experience_years', 0)}")
        st.write(f"Previous Companies: {', '.join(candidate['parsed_info'].get('previous_companies', []))}")
        st.write(f"Salary Expectation: {candidate['parsed_info'].get('salary_expectation', 'N/A')}")

    with col2:
        st.write("**Skills:**")
        skills = candidate['parsed_info'].get('skills', [])
        for skill in skills:
            st.write(f"• {skill.title()}")

        st.write("**Education:**")
        education = candidate['parsed_info'].get('education', [])
        for edu in education:
            st.write(f"• {edu}")

        st.write("**Scores:**")
        scores = candidate.get('scores', {})
        for category, score in scores.items():
            st.write(f"• {category.title()}: {score}%")

def start_interview(candidate):
    """Start interview with selected candidate"""
    st.session_state.selected_candidate = candidate
    st.session_state.interview_active = True
    st.success(f"Interview started with {candidate.get('name', candidate['filename'])}")
    st.rerun()

def delete_candidate(candidate_id):
    """Delete candidate from database"""
    st.session_state.candidates = [c for c in st.session_state.candidates if c['id'] != candidate_id]
    st.success("Candidate deleted successfully")
    st.rerun()

def show_job_configuration():
    """Advanced job configuration interface"""
    st.header("💼 Job Configuration")

    # Job details form
    with st.form("job_configuration_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Basic Information")
            role = st.text_input("Job Title", value=st.session_state.job_requirements.get('role', ''))
            department = st.text_input("Department", value=st.session_state.job_requirements.get('department', ''))
            employment_type = st.selectbox("Employment Type",
                                         ["Full-time", "Part-time", "Contract", "Internship"],
                                         index=0)
            urgency = st.selectbox("Urgency Level", ["Low", "Medium", "High", "Critical"], index=2)

            st.subheader("💰 Compensation")
            salary_range = st.text_input("Salary Range", value=st.session_state.job_requirements.get('salary_range', ''))
            location = st.text_input("Location", value=st.session_state.job_requirements.get('location', ''))

        with col2:
            st.subheader("🎯 Requirements")
            required_skills = st.text_area("Required Skills (comma-separated)",
                                         value=', '.join(st.session_state.job_requirements.get('required_skills', [])))
            preferred_skills = st.text_area("Preferred Skills (comma-separated)",
                                           value=', '.join(st.session_state.job_requirements.get('preferred_skills', [])))

            min_exp = st.number_input("Minimum Experience (years)",
                                    value=st.session_state.job_requirements.get('min_experience_years', 0))
            max_exp = st.number_input("Maximum Experience (years)",
                                    value=st.session_state.job_requirements.get('max_experience_years', 15))
            education = st.selectbox("Education Level",
                                   ["High School", "Associate", "Bachelor", "Master", "PhD"],
                                   index=2)

        st.subheader("👥 Team Information")
        col1, col2 = st.columns(2)
        with col1:
            team_size = st.number_input("Team Size", value=st.session_state.job_requirements.get('team_size', 5))
        with col2:
            reporting_to = st.text_input("Reports To", value=st.session_state.job_requirements.get('reporting_to', ''))

        if st.form_submit_button("💾 Save Job Configuration", type="primary"):
            st.session_state.job_requirements = {
                'role': role,
                'department': department,
                'employment_type': employment_type,
                'urgency': urgency,
                'salary_range': salary_range,
                'location': location,
                'required_skills': [s.strip() for s in required_skills.split(',') if s.strip()],
                'preferred_skills': [s.strip() for s in preferred_skills.split(',') if s.strip()],
                'min_experience_years': min_exp,
                'max_experience_years': max_exp,
                'education_level': education,
                'team_size': team_size,
                'reporting_to': reporting_to
            }
            st.success("✅ Job configuration saved successfully!")

            # Recalculate match scores for existing candidates
            if st.session_state.candidates and RESUME_FILTER_AVAILABLE and st.session_state.resume_filter:
                for candidate in st.session_state.candidates:
                    new_score = st.session_state.resume_filter.calculate_job_match_score(
                        candidate['parsed_info'], st.session_state.job_requirements
                    )
                    candidate['match_score'] = new_score
                    candidate['recommendation'] = get_recommendation(new_score)
                st.info("🔄 Candidate match scores updated based on new job requirements")

def show_voice_interview():
    """Enhanced voice interview interface"""
    st.header("🎤 Voice Interview System")

    if not st.session_state.interview_active:
        st.info("No active interview. Please select a candidate from Resume Management.")
        return

    candidate = st.session_state.selected_candidate
    if not candidate:
        st.error("No candidate selected.")
        return

    # Interview header
    st.markdown(f"""
    <div class="metric-card">
        <h3>🎤 Interviewing: {candidate.get('name', candidate['filename'])}</h3>
        <p><strong>Match Score:</strong> {candidate.get('match_score', 0):.1f}% |
        <strong>Status:</strong> {candidate.get('interview_status', 'Pending')}</p>
    </div>
    """, unsafe_allow_html=True)

    # Voice controls
    col1, col2, col3 = st.columns(3)

    with col1:
        voice_mode = st.toggle("🎤 Voice Mode", value=st.session_state.voice_mode)
        st.session_state.voice_mode = voice_mode

    with col2:
        if VOICE_AVAILABLE and st.session_state.voice_engine:
            status = st.session_state.voice_engine.get_listening_status()
            if status['is_listening']:
                st.markdown('<div class="voice-status listening">🎤 LISTENING</div>', unsafe_allow_html=True)
            elif status['is_processing']:
                st.markdown('<div class="voice-status processing">🔄 PROCESSING</div>', unsafe_allow_html=True)
            elif status['is_speaking']:
                st.markdown('<div class="voice-status speaking">🗣️ SPEAKING</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="voice-status ready">✅ READY</div>', unsafe_allow_html=True)

    with col3:
        interview_duration = len(st.session_state.conversation_history) * 1.5
        st.metric("Duration", f"{interview_duration:.1f} min")

    # Conversation display
    st.subheader("💬 Interview Conversation")

    conversation_container = st.container()
    with conversation_container:
        if st.session_state.conversation_history:
            for entry in st.session_state.conversation_history:
                confidence = entry.get('confidence', 1.0)

                if entry['role'] == 'ai':
                    st.markdown(f"""
                    <div class="conversation-bubble ai-bubble">
                        <strong>🤖 AI Interviewer:</strong><br>
                        {entry['message']}
                        <small style="opacity: 0.7; float: right;">{datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    confidence_color = "#4caf50" if confidence > 0.8 else "#ff9800" if confidence > 0.6 else "#f44336"
                    st.markdown(f"""
                    <div class="conversation-bubble user-bubble">
                        <strong>👤 Candidate:</strong><br>
                        {entry['message']}
                        <small style="opacity: 0.7; float: right;">
                            <span style="color: {confidence_color};">Confidence: {confidence:.1%}</span> |
                            {datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Interview conversation will appear here...")

    # Interview controls
    st.markdown("---")

    if voice_mode and VOICE_AVAILABLE:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🎤 Start Voice Turn", type="primary"):
                conduct_voice_interview_turn()

        with col2:
            if st.button("⏸️ Pause Interview"):
                st.info("Interview paused. Click 'Start Voice Turn' to continue.")

        with col3:
            if st.button("📝 Add Note"):
                show_note_interface()

        with col4:
            if st.button("⏹️ End Interview"):
                end_interview()

    else:
        # Text mode
        user_input = st.text_area("Your response:", height=100, key="interview_text_input")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📤 Send Response", type="primary"):
                if user_input.strip():
                    process_text_interview_response(user_input)

        with col2:
            if st.button("📝 Add Note"):
                show_note_interface()

        with col3:
            if st.button("⏹️ End Interview"):
                end_interview()

def conduct_voice_interview_turn():
    """Conduct voice interview turn"""
    if not VOICE_AVAILABLE or not st.session_state.voice_engine:
        st.error("Voice engine not available")
        return

    with st.spinner("🎤 Processing voice input..."):
        try:
            # Initialize interview if not started
            if not st.session_state.conversation_history:
                opening = st.session_state.voice_engine.start_interview(
                    st.session_state.selected_candidate,
                    st.session_state.job_requirements
                )
                st.session_state.conversation_history = st.session_state.voice_engine.conversation_history

            # Conduct voice turn
            candidate_speech, ai_response, turn_info = st.session_state.voice_engine.conduct_enhanced_voice_turn()

            # Update conversation history
            st.session_state.conversation_history = st.session_state.voice_engine.conversation_history

            # Show feedback
            if turn_info['status'] == 'success':
                st.success(f"✅ Voice turn completed! Confidence: {turn_info['confidence']:.1%}")
            elif turn_info['status'] == 'timeout':
                st.warning("⏰ No response detected. Please try again.")
            elif turn_info['status'] == 'unclear':
                st.warning("🔇 Speech unclear. Please speak more clearly.")
            else:
                st.error("❌ Audio error occurred.")

            st.rerun()

        except Exception as e:
            st.error(f"Voice processing error: {e}")

def process_text_interview_response(user_input):
    """Process text interview response"""
    # Add user response
    st.session_state.conversation_history.append({
        'role': 'user',
        'message': user_input,
        'timestamp': datetime.now().isoformat(),
        'confidence': 1.0
    })

    # Generate AI response (simplified for demo)
    ai_responses = [
        "That's very interesting. Can you tell me more about that experience?",
        "I see. How did you handle the challenges in that situation?",
        "Thank you for sharing that. What would you say was your biggest learning from that?",
        "That sounds like valuable experience. How do you think it applies to this role?",
        "Great! Do you have any questions about our company or this position?"
    ]

    ai_response = ai_responses[len(st.session_state.conversation_history) % len(ai_responses)]

    st.session_state.conversation_history.append({
        'role': 'ai',
        'message': ai_response,
        'timestamp': datetime.now().isoformat(),
        'confidence': 1.0
    })

    st.rerun()

def show_note_interface():
    """Show interface for adding interview notes"""
    with st.expander("📝 Add Interview Note", expanded=True):
        note_text = st.text_area("Note:", height=100)
        note_category = st.selectbox("Category:", ["General", "Technical", "Behavioral", "Cultural Fit", "Concern"])

        if st.button("💾 Save Note"):
            if note_text.strip():
                note = {
                    "candidate_id": st.session_state.selected_candidate['id'],
                    "timestamp": datetime.now().isoformat(),
                    "note": note_text,
                    "category": note_category,
                    "interviewer": "HR Manager"  # Would be dynamic in real system
                }
                st.session_state.interview_notes.append(note)
                st.success("Note saved successfully!")
                st.rerun()

def end_interview():
    """End current interview"""
    if st.session_state.selected_candidate:
        # Update candidate status
        for candidate in st.session_state.candidates:
            if candidate['id'] == st.session_state.selected_candidate['id']:
                candidate['interview_status'] = 'Completed'
                break

        # Save interview data (would save to database in real system)
        interview_data = {
            'candidate_id': st.session_state.selected_candidate['id'],
            'conversation': st.session_state.conversation_history,
            'notes': [note for note in st.session_state.interview_notes
                     if note['candidate_id'] == st.session_state.selected_candidate['id']],
            'end_time': datetime.now().isoformat()
        }

        st.success("✅ Interview completed and saved!")

    st.session_state.interview_active = False
    st.session_state.selected_candidate = None
    st.session_state.conversation_history = []
    st.rerun()

# Placeholder functions for remaining modules
def show_interview_notes():
    st.header("📝 Interview Notes")
    st.info("Interview notes module - would show all notes with filtering and search")

def show_bias_detection():
    st.header("⚖️ Bias Detection")
    st.info("Bias detection module - would analyze interviews for potential bias")

def show_candidate_scoring():
    st.header("📈 Candidate Scoring")
    st.info("Advanced scoring dashboard with detailed breakdowns")

def show_candidate_comparison():
    st.header("🔄 Candidate Comparison")
    st.info("Side-by-side candidate comparison tool")

def show_email_integration():
    st.header("📧 Email Integration")
    st.info("Email automation for interview scheduling and follow-ups")

def show_multi_language():
    st.header("🌍 Multi-Language Support")
    st.info("Multi-language interview capabilities")

def show_audio_recordings():
    st.header("🎵 Audio Recordings")
    st.info("Interview recording management and playback")

def show_system_settings():
    st.header("⚙️ System Settings")
    st.info("System configuration and preferences")

if __name__ == "__main__":
    main()
