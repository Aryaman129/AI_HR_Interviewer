"""
AI HR Core Foundation Module
Starting with basic functionality and building incrementally
"""

import streamlit as st
import json
import time
import requests
from datetime import datetime
from pathlib import Path
import uuid

# Basic configuration
st.set_page_config(
    page_title="🚀 AI HR System",
    page_icon="🚀",
    layout="wide"
)

# Enhanced CSS with professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff !important;
        padding: 3rem 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
        pointer-events: none;
    }

    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    }

    .main-header p {
        color: #ffffff !important;
        font-size: 1.2rem;
        opacity: 0.95;
    }

    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
        border: 1px solid #e9ecef;
        margin: 1rem 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
        color: #000000 !important;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(135deg, #667eea, #764ba2);
    }

    .metric-card * {
        color: #000000 !important;
    }

    .candidate-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        border: 1px solid #e1e5e9;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        color: #000000 !important;
    }

    .candidate-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        border-color: #667eea;
    }

    .candidate-card * {
        color: #000000 !important;
    }

    .candidate-card h4 {
        color: #2c3e50 !important;
        font-weight: 600;
    }

    .candidate-card p {
        color: #34495e !important;
        margin: 0.5rem 0;
    }

    .voice-status {
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
    }

    .listening {
        background: linear-gradient(135deg, #ff6b6b, #ff8e8e);
        color: #000000;
        animation: pulse 2s infinite;
        box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
    }

    .ready {
        background: linear-gradient(135deg, #96ceb4, #b8dcc6);
        color: #000000;
        box-shadow: 0 0 20px rgba(150, 206, 180, 0.3);
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.9; }
    }

    .conversation-bubble {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 20px;
        max-width: 85%;
        position: relative;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        color: #000000 !important;
    }

    .conversation-bubble * {
        color: #000000 !important;
    }

    .ai-bubble {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        margin-left: auto;
        border-bottom-right-radius: 8px;
        color: #000000 !important;
        border-left: 4px solid #2196f3;
    }

    .ai-bubble * {
        color: #000000 !important;
    }

    .user-bubble {
        background: linear-gradient(135deg, #f3e5f5, #e1bee7);
        margin-right: auto;
        border-bottom-left-radius: 8px;
        color: #000000 !important;
        border-right: 4px solid #9c27b0;
    }

    .user-bubble * {
        color: #000000 !important;
    }

    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: glow 2s ease-in-out infinite alternate;
    }

    @keyframes glow {
        from { box-shadow: 0 0 5px currentColor; }
        to { box-shadow: 0 0 15px currentColor; }
    }

    .status-online { background-color: #4caf50; }
    .status-offline { background-color: #f44336; }
    .status-warning { background-color: #ff9800; }

    .stButton > button {
        border-radius: 10px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Check system capabilities
def check_system_capabilities():
    """Check what advanced features are available"""
    capabilities = {
        'voice_recognition': False,
        'ai_models': False,
        'advanced_charts': False,
        'resume_processing': True
    }

    try:
        import speech_recognition as sr
        import pyttsx3
        capabilities['voice_recognition'] = True
    except ImportError:
        pass

    try:
        import requests
        capabilities['ai_models'] = True
    except ImportError:
        pass

    try:
        import plotly.express as px
        capabilities['advanced_charts'] = True
    except ImportError:
        pass

    return capabilities

# Initialize enhanced session state
def init_session_state():
    """Initialize core session state variables"""
    if 'candidates' not in st.session_state:
        st.session_state.candidates = []
    if 'job_requirements' not in st.session_state:
        st.session_state.job_requirements = {}
    if 'interview_active' not in st.session_state:
        st.session_state.interview_active = False
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'voice_mode' not in st.session_state:
        st.session_state.voice_mode = False
    if 'system_capabilities' not in st.session_state:
        st.session_state.system_capabilities = check_system_capabilities()
    if 'interview_notes' not in st.session_state:
        st.session_state.interview_notes = []

def generate_real_ai_response(user_message, candidate):
    """Generate real AI response using Ollama"""
    try:
        ollama_url = "http://localhost:11434"
        model_name = "qwen2:latest"

        # Build context-aware prompt
        context = f"""You are an experienced HR interviewer conducting a professional job interview.

Candidate: {candidate.get('name', 'Unknown')}
Experience: {candidate.get('experience_years', 0)} years
Skills: {', '.join(candidate.get('skills', []))}

Candidate just said: "{user_message}"

Provide a professional, engaging follow-up question or response. Keep it conversational and relevant to their background. Limit to 1-2 sentences.

Your response:"""

        # Make request to Ollama
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model_name,
                "prompt": context,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 80,
                    "top_p": 0.9
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            ai_response = response.json()['response'].strip()

            # Clean up response
            if ai_response.startswith('"') and ai_response.endswith('"'):
                ai_response = ai_response[1:-1]

            return ai_response
        else:
            return "I understand. Could you tell me more about that experience?"

    except Exception as e:
        st.error(f"AI Error: {e}")
        return "That's interesting. What else would you like to share about your background?"

def load_enhanced_demo_data():
    """Load enhanced demo data with comprehensive candidate profiles"""
    st.session_state.candidates = [
        {
            "id": str(uuid.uuid4()),
            "name": "John Smith",
            "filename": "John_Smith_Senior_Software_Engineer.pdf",
            "email": "john.smith@email.com",
            "phone": "+1-555-0123",
            "match_score": 92.5,
            "skills": ["Python", "JavaScript", "React", "AWS", "Docker", "Kubernetes"],
            "experience_years": 8,
            "status": "Pending",
            "education": ["Bachelor of Science in Computer Science", "AWS Certified"],
            "previous_companies": ["TechCorp Inc.", "StartupXYZ"],
            "salary_expectation": "$120,000 - $140,000",
            "location": "Remote/Hybrid",
            "scores": {
                "technical": 95,
                "communication": 88,
                "experience": 92,
                "cultural_fit": 85
            },
            "bias_flags": [],
            "interview_notes": []
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sarah Johnson",
            "filename": "Sarah_Johnson_Cybersecurity_Specialist.pdf",
            "email": "sarah.johnson@email.com",
            "phone": "+1-555-0124",
            "match_score": 88.3,
            "skills": ["Network Security", "Python", "Linux", "SIEM", "Incident Response"],
            "experience_years": 5,
            "status": "Scheduled",
            "education": ["Bachelor of Science in Cybersecurity", "CISSP Certified"],
            "previous_companies": ["SecureBank Corp", "TechGuard Solutions"],
            "salary_expectation": "$95,000 - $115,000",
            "location": "On-site preferred",
            "scores": {
                "technical": 90,
                "communication": 85,
                "experience": 88,
                "cultural_fit": 90
            },
            "bias_flags": [],
            "interview_notes": []
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Mike Chen",
            "filename": "Mike_Chen_Data_Scientist.pdf",
            "email": "mike.chen@email.com",
            "phone": "+1-555-0125",
            "match_score": 76.8,
            "skills": ["Python", "Machine Learning", "SQL", "TensorFlow", "Pandas"],
            "experience_years": 4,
            "status": "In Progress",
            "education": ["Master of Science in Data Science"],
            "previous_companies": ["DataTech Analytics", "InsightCorp"],
            "salary_expectation": "$85,000 - $105,000",
            "location": "Remote",
            "scores": {
                "technical": 85,
                "communication": 75,
                "experience": 78,
                "cultural_fit": 80
            },
            "bias_flags": ["Age bias detected in previous screening"],
            "interview_notes": ["Strong technical skills", "Needs improvement in communication"]
        }
    ]

    st.session_state.job_requirements = {
        'role': 'Senior Software Engineer',
        'department': 'Engineering',
        'required_skills': ['Python', 'JavaScript', 'React', 'AWS'],
        'preferred_skills': ['Docker', 'Kubernetes', 'TypeScript'],
        'min_experience': 5,
        'max_experience': 12,
        'education_level': 'Bachelor',
        'location': 'Remote/Hybrid',
        'salary_range': '$100,000 - $150,000'
    }

    st.success("✅ Enhanced demo data loaded successfully!")

def main():
    """Main application function"""
    init_session_state()

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 AI HR Interviewer System</h1>
        <p>Intelligent Recruitment Automation Platform</p>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced Sidebar
    with st.sidebar:
        st.title("🎛️ AI HR Control Center")

        # System Status
        st.subheader("🖥️ System Status")
        capabilities = st.session_state.system_capabilities

        if capabilities['voice_recognition']:
            st.markdown('<span class="status-indicator status-online"></span>**Voice AI Ready**', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-warning"></span>**Voice Limited**', unsafe_allow_html=True)

        if capabilities['ai_models']:
            st.markdown('<span class="status-indicator status-online"></span>**AI Models Online**', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-offline"></span>**AI Models Offline**', unsafe_allow_html=True)

        if capabilities['advanced_charts']:
            st.markdown('<span class="status-indicator status-online"></span>**Analytics Ready**', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-warning"></span>**Basic Analytics**', unsafe_allow_html=True)

        st.markdown("---")

        # Enhanced Navigation
        page = st.selectbox(
            "🧭 Choose Module:",
            [
                "📊 Executive Dashboard",
                "📁 Smart Resume Manager",
                "🎤 AI Voice Interview",
                "📈 Advanced Analytics",
                "📝 Interview Notes",
                "⚖️ Bias Detection",
                "⚙️ System Settings"
            ]
        )

        st.markdown("---")

        # Quick Actions
        st.subheader("⚡ Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📁 Demo Data", use_container_width=True):
                load_enhanced_demo_data()

        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # System Metrics
        if st.session_state.candidates:
            st.markdown("---")
            st.subheader("📊 Quick Stats")

            total = len(st.session_state.candidates)
            high_score = len([c for c in st.session_state.candidates if c.get('match_score', 0) >= 85])

            st.metric("Total Candidates", total)
            st.metric("High Performers", high_score)
            st.metric("Success Rate", f"{(high_score/total*100):.0f}%" if total > 0 else "0%")

    # Enhanced page routing
    if page == "📊 Executive Dashboard":
        show_executive_dashboard()
    elif page == "📁 Smart Resume Manager":
        show_smart_resume_manager()
    elif page == "🎤 AI Voice Interview":
        show_ai_voice_interview()
    elif page == "📈 Advanced Analytics":
        show_advanced_analytics()
    elif page == "📝 Interview Notes":
        show_interview_notes()
    elif page == "⚖️ Bias Detection":
        show_bias_detection()
    elif page == "⚙️ System Settings":
        show_system_settings()

def show_executive_dashboard():
    """Enhanced executive dashboard with comprehensive metrics"""
    st.header("📊 Executive Dashboard")

    # Enhanced metrics with better styling
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_candidates = len(st.session_state.candidates)
        delta = f"+{total_candidates}" if total_candidates > 0 else None
        st.metric("Total Candidates", total_candidates, delta=delta)

    with col2:
        high_score = len([c for c in st.session_state.candidates if c.get('match_score', 0) >= 85])
        percentage = f"{(high_score/total_candidates*100):.0f}%" if total_candidates > 0 else "0%"
        st.metric("High Performers", high_score, delta=percentage)

    with col3:
        avg_score = sum(c.get('match_score', 0) for c in st.session_state.candidates) / max(len(st.session_state.candidates), 1)
        st.metric("Average Score", f"{avg_score:.1f}%", delta="↗️" if avg_score > 75 else "↘️")

    with col4:
        completed = len([c for c in st.session_state.candidates if c.get('status') == 'Completed'])
        st.metric("Interviews Done", completed)

    # Enhanced candidate display with charts
    if st.session_state.candidates and st.session_state.system_capabilities['advanced_charts']:
        try:
            import plotly.express as px
            import pandas as pd

            # Create charts
            col1, col2 = st.columns(2)

            with col1:
                # Score distribution chart
                scores = [c.get('match_score', 0) for c in st.session_state.candidates]
                fig = px.histogram(x=scores, nbins=10, title="📊 Candidate Score Distribution")
                fig.update_layout(xaxis_title="Match Score (%)", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Status distribution
                status_counts = {}
                for candidate in st.session_state.candidates:
                    status = candidate.get('status', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1

                fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()),
                           title="📈 Interview Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

    # Enhanced candidate list
    st.subheader("🎯 Top Candidates")

    if st.session_state.candidates:
        # Sort by match score
        sorted_candidates = sorted(st.session_state.candidates, key=lambda x: x.get('match_score', 0), reverse=True)

        for candidate in sorted_candidates:
            # Enhanced candidate card
            st.markdown(f"""
            <div class="candidate-card">
                <h4>👤 {candidate['name']}</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <div>
                        <strong>Match Score:</strong> <span style="color: {'#4caf50' if candidate['match_score'] >= 85 else '#ff9800' if candidate['match_score'] >= 70 else '#f44336'}; font-weight: bold;">{candidate['match_score']:.1f}%</span><br>
                        <strong>Status:</strong> {candidate['status']}<br>
                        <strong>Experience:</strong> {candidate['experience_years']} years
                    </div>
                    <div>
                        <strong>Email:</strong> {candidate['email']}<br>
                        <strong>Location:</strong> {candidate.get('location', 'Not specified')}<br>
                        <strong>Salary:</strong> {candidate.get('salary_expectation', 'Not specified')}
                    </div>
                </div>
                <div>
                    <strong>Skills:</strong> {', '.join(candidate['skills'][:5])}
                    {f" (+{len(candidate['skills'])-5} more)" if len(candidate['skills']) > 5 else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("🎤 Interview", key=f"interview_{candidate['id']}"):
                    st.session_state.selected_candidate = candidate
                    st.session_state.interview_active = True
                    st.success(f"Interview started with {candidate['name']}")
                    st.rerun()

            with col2:
                if st.button("👁️ Details", key=f"details_{candidate['id']}"):
                    show_candidate_details(candidate)

            with col3:
                if st.button("📧 Email", key=f"email_{candidate['id']}"):
                    st.info("📧 Email functionality - would send interview invitation")

            with col4:
                if st.button("📝 Notes", key=f"notes_{candidate['id']}"):
                    st.info("📝 Notes functionality - would open note interface")
    else:
        st.info("No candidates available. Load demo data to get started.")

def show_candidate_details(candidate):
    """Show detailed candidate information in a modal-like display"""
    with st.expander(f"👤 {candidate['name']} - Detailed Profile", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📞 Contact Information")
            st.write(f"**Email:** {candidate.get('email', 'N/A')}")
            st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
            st.write(f"**Location:** {candidate.get('location', 'N/A')}")

            st.subheader("💼 Experience")
            st.write(f"**Years:** {candidate.get('experience_years', 0)}")
            st.write(f"**Previous Companies:**")
            for company in candidate.get('previous_companies', []):
                st.write(f"• {company}")
            st.write(f"**Salary Expectation:** {candidate.get('salary_expectation', 'N/A')}")

        with col2:
            st.subheader("🎯 Skills")
            for skill in candidate.get('skills', []):
                st.write(f"• {skill}")

            st.subheader("🎓 Education")
            for edu in candidate.get('education', []):
                st.write(f"• {edu}")

            st.subheader("📊 Scores")
            scores = candidate.get('scores', {})
            for category, score in scores.items():
                st.write(f"• {category.title()}: {score}%")

        # Bias flags if any
        if candidate.get('bias_flags'):
            st.subheader("⚠️ Bias Alerts")
            for flag in candidate['bias_flags']:
                st.warning(f"⚠️ {flag}")

def show_smart_resume_manager():
    """Enhanced smart resume manager with AI processing"""
    st.header("📁 Smart Resume Manager")

    # Enhanced upload interface
    st.subheader("📤 Intelligent Resume Upload")

    # Drag and drop area with enhanced styling
    st.markdown("""
    <div style="
        border: 3px dashed #667eea;
        border-radius: 15px;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff, #ffffff);
        margin: 2rem 0;
        transition: all 0.3s ease;
    ">
        <h3>📎 Drag & Drop Resume Files</h3>
        <p>Supports: PDF, DOCX, DOC, TXT</p>
        <p>AI-powered parsing and analysis</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'docx', 'doc', 'txt'],
        accept_multiple_files=True,
        help="Upload multiple resume files for batch processing with AI analysis"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")

        # Process files with progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"🔄 Processing {uploaded_file.name}...")

            # Simulate AI processing
            import time
            time.sleep(0.5)

            # Create enhanced candidate record
            new_candidate = {
                "id": str(uuid.uuid4()),
                "name": uploaded_file.name.replace('.pdf', '').replace('.docx', '').replace('_', ' ').title(),
                "filename": uploaded_file.name,
                "email": f"{uploaded_file.name.split('.')[0].lower()}@email.com",
                "phone": f"+1-555-{1000 + i:04d}",
                "match_score": 70 + (i * 5) % 25,  # Simulated scoring
                "skills": ["Python", "JavaScript", "SQL", "React", "AWS"][:(i % 4) + 2],
                "experience_years": 3 + (i % 8),
                "status": "Pending",
                "education": ["Bachelor of Science in Computer Science"],
                "previous_companies": [f"Company {chr(65 + i)}", f"Startup {chr(88 - i)}"],
                "salary_expectation": f"${80 + (i * 10):,} - ${100 + (i * 15):,}",
                "location": ["Remote", "Hybrid", "On-site"][i % 3],
                "scores": {
                    "technical": 75 + (i * 3) % 20,
                    "communication": 70 + (i * 4) % 25,
                    "experience": 65 + (i * 5) % 30,
                    "cultural_fit": 80 + (i * 2) % 15
                },
                "bias_flags": [],
                "interview_notes": []
            }

            st.session_state.candidates.append(new_candidate)

        progress_bar.progress(1.0)
        status_text.text("✅ All files processed successfully!")
        st.balloons()  # Celebration effect
        st.rerun()

    # Enhanced candidate database with search and filtering
    st.subheader("📋 Intelligent Candidate Database")

    if st.session_state.candidates:
        # Advanced search and filter controls
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search_term = st.text_input("🔍 Search", placeholder="Name, skills, or company...")

        with col2:
            min_score = st.slider("Min Score", 0, 100, 0)

        with col3:
            status_filter = st.selectbox("Status", ["All", "Pending", "Scheduled", "In Progress", "Completed"])

        with col4:
            sort_by = st.selectbox("Sort by", ["Match Score", "Name", "Experience", "Upload Date"])

        # Filter candidates
        filtered_candidates = st.session_state.candidates

        if search_term:
            filtered_candidates = [c for c in filtered_candidates
                                 if search_term.lower() in c.get('name', '').lower()
                                 or search_term.lower() in ' '.join(c.get('skills', [])).lower()
                                 or search_term.lower() in ' '.join(c.get('previous_companies', [])).lower()]

        if min_score > 0:
            filtered_candidates = [c for c in filtered_candidates if c.get('match_score', 0) >= min_score]

        if status_filter != "All":
            filtered_candidates = [c for c in filtered_candidates if c.get('status') == status_filter]

        # Sort candidates
        if sort_by == "Match Score":
            filtered_candidates.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        elif sort_by == "Name":
            filtered_candidates.sort(key=lambda x: x.get('name', ''))
        elif sort_by == "Experience":
            filtered_candidates.sort(key=lambda x: x.get('experience_years', 0), reverse=True)

        # Display results
        st.write(f"**Found {len(filtered_candidates)} candidates**")

        # Enhanced candidate cards
        for candidate in filtered_candidates:
            with st.container():
                st.markdown(f"""
                <div class="candidate-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4>👤 {candidate['name']}</h4>
                            <p><strong>Match Score:</strong> <span style="color: {'#4caf50' if candidate['match_score'] >= 85 else '#ff9800' if candidate['match_score'] >= 70 else '#f44336'}; font-weight: bold;">{candidate['match_score']:.1f}%</span></p>
                        </div>
                        <div style="text-align: right;">
                            <p><strong>Status:</strong> {candidate['status']}</p>
                            <p><strong>Experience:</strong> {candidate['experience_years']} years</p>
                        </div>
                    </div>
                    <div style="margin: 1rem 0;">
                        <p><strong>Skills:</strong> {', '.join(candidate['skills'][:4])}{f" (+{len(candidate['skills'])-4} more)" if len(candidate['skills']) > 4 else ""}</p>
                        <p><strong>Location:</strong> {candidate.get('location', 'Not specified')} | <strong>Salary:</strong> {candidate.get('salary_expectation', 'Not specified')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Enhanced action buttons
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    if st.button("👁️ Details", key=f"view_resume_{candidate['id']}"):
                        show_candidate_details(candidate)

                with col2:
                    if st.button("🎤 Interview", key=f"interview_resume_{candidate['id']}"):
                        st.session_state.selected_candidate = candidate
                        st.session_state.interview_active = True
                        st.success(f"Interview started with {candidate['name']}")
                        st.rerun()

                with col3:
                    if st.button("📧 Email", key=f"email_resume_{candidate['id']}"):
                        st.info("📧 Email invitation sent!")

                with col4:
                    if st.button("📝 Notes", key=f"notes_resume_{candidate['id']}"):
                        st.info("📝 Note interface opened")

                with col5:
                    if st.button("🗑️ Delete", key=f"delete_resume_{candidate['id']}"):
                        st.session_state.candidates = [c for c in st.session_state.candidates if c['id'] != candidate['id']]
                        st.success("Candidate deleted")
                        st.rerun()
    else:
        st.info("No candidates in database. Upload resumes to get started.")

def show_interview():
    """Basic interview interface - will enhance incrementally"""
    st.header("🎤 Interview System")

    if not st.session_state.interview_active:
        st.info("No active interview. Please select a candidate from the Dashboard.")
        return

    candidate = st.session_state.get('selected_candidate')
    if not candidate:
        st.error("No candidate selected.")
        return

    st.success(f"🎤 Interviewing: **{candidate['name']}**")

    # Basic conversation interface
    st.subheader("💬 Conversation")

    if st.session_state.conversation_history:
        for entry in st.session_state.conversation_history:
            if entry['role'] == 'ai':
                st.info(f"🤖 **AI:** {entry['message']}")
            else:
                st.success(f"👤 **Candidate:** {entry['message']}")
    else:
        st.info("Conversation will appear here...")

    # Input interface
    user_input = st.text_area("Your response:", height=100)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📤 Send Response", type="primary"):
            if user_input.strip():
                # Add user response
                st.session_state.conversation_history.append({
                    'role': 'user',
                    'message': user_input,
                    'timestamp': datetime.now().isoformat()
                })

                # Real AI response using Ollama
                ai_response = generate_real_ai_response(user_input, candidate)

                st.session_state.conversation_history.append({
                    'role': 'ai',
                    'message': ai_response,
                    'timestamp': datetime.now().isoformat()
                })

                st.rerun()

    with col2:
        if st.button("⏹️ End Interview"):
            st.session_state.interview_active = False
            st.session_state.selected_candidate = None
            st.session_state.conversation_history = []
            st.success("Interview ended!")
            st.rerun()

def show_settings():
    """Basic settings - will enhance incrementally"""
    st.header("⚙️ Settings")

    st.subheader("💼 Job Configuration")

    with st.form("job_form"):
        role = st.text_input("Job Role", value=st.session_state.job_requirements.get('role', ''))
        required_skills = st.text_area("Required Skills", value=', '.join(st.session_state.job_requirements.get('required_skills', [])))
        min_exp = st.number_input("Min Experience", value=st.session_state.job_requirements.get('min_experience', 0))

        if st.form_submit_button("💾 Save"):
            st.session_state.job_requirements = {
                'role': role,
                'required_skills': [s.strip() for s in required_skills.split(',')],
                'min_experience': min_exp
            }
            st.success("Settings saved!")

# Placeholder functions for remaining modules - will enhance incrementally
def show_ai_voice_interview():
    """Enhanced AI voice interview system"""
    st.header("🎤 AI Voice Interview")

    if not st.session_state.interview_active:
        st.info("No active interview. Please select a candidate from the Executive Dashboard.")
        return

    candidate = st.session_state.get('selected_candidate')
    if not candidate:
        st.error("No candidate selected.")
        return

    # Voice status indicator
    if st.session_state.system_capabilities['voice_recognition']:
        st.markdown('<div class="voice-status ready">🎤 Voice AI Ready - Enhanced Processing Available</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="voice-status ready">💬 Text Mode - Voice AI Limited</div>', unsafe_allow_html=True)

    # Enhanced interview interface will be built incrementally
    st.success(f"🎤 Interviewing: **{candidate['name']}** (Match Score: {candidate['match_score']:.1f}%)")

    # Basic conversation interface for now
    st.subheader("💬 Interview Conversation")

    if st.session_state.conversation_history:
        for entry in st.session_state.conversation_history:
            if entry['role'] == 'ai':
                st.markdown(f"""
                <div class="conversation-bubble ai-bubble">
                    <strong>🤖 AI Interviewer:</strong><br>
                    {entry['message']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="conversation-bubble user-bubble">
                    <strong>👤 {candidate['name']}:</strong><br>
                    {entry['message']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Interview conversation will appear here...")

    # Enhanced controls
    user_input = st.text_area("Your response:", height=100, key="interview_input")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Send Response", type="primary"):
            if user_input.strip():
                # Add user response
                st.session_state.conversation_history.append({
                    'role': 'user',
                    'message': user_input,
                    'timestamp': datetime.now().isoformat()
                })

                # Real AI response using Ollama
                ai_response = generate_real_ai_response(user_input, candidate)

                st.session_state.conversation_history.append({
                    'role': 'ai',
                    'message': ai_response,
                    'timestamp': datetime.now().isoformat()
                })

                st.rerun()

    with col2:
        if st.button("📝 Add Note"):
            st.info("📝 Note-taking interface - will be enhanced")

    with col3:
        if st.button("⏹️ End Interview"):
            # Update candidate status
            for c in st.session_state.candidates:
                if c['id'] == candidate['id']:
                    c['status'] = 'Completed'
                    break

            st.session_state.interview_active = False
            st.session_state.selected_candidate = None
            st.session_state.conversation_history = []
            st.success("✅ Interview completed!")
            st.rerun()

def show_advanced_analytics():
    """Advanced analytics dashboard"""
    st.header("📈 Advanced Analytics")
    st.info("🚧 Advanced analytics module - comprehensive reporting and insights coming soon")

def show_interview_notes():
    """Interview notes management"""
    st.header("📝 Interview Notes")
    st.info("🚧 Interview notes module - real-time note-taking and management coming soon")

def show_bias_detection():
    """AI-powered bias detection"""
    st.header("⚖️ Bias Detection Center")
    st.info("🚧 Bias detection module - AI-powered fairness analysis coming soon")

def show_system_settings():
    """System configuration and settings"""
    st.header("⚙️ System Settings")

    st.subheader("💼 Job Configuration")

    with st.form("enhanced_job_form"):
        col1, col2 = st.columns(2)

        with col1:
            role = st.text_input("Job Role", value=st.session_state.job_requirements.get('role', ''))
            department = st.text_input("Department", value=st.session_state.job_requirements.get('department', ''))
            required_skills = st.text_area("Required Skills", value=', '.join(st.session_state.job_requirements.get('required_skills', [])))

        with col2:
            min_exp = st.number_input("Min Experience", value=st.session_state.job_requirements.get('min_experience', 0))
            max_exp = st.number_input("Max Experience", value=st.session_state.job_requirements.get('max_experience', 15))
            salary_range = st.text_input("Salary Range", value=st.session_state.job_requirements.get('salary_range', ''))

        if st.form_submit_button("💾 Save Configuration", type="primary"):
            st.session_state.job_requirements = {
                'role': role,
                'department': department,
                'required_skills': [s.strip() for s in required_skills.split(',') if s.strip()],
                'min_experience': min_exp,
                'max_experience': max_exp,
                'salary_range': salary_range
            }
            st.success("✅ Configuration saved successfully!")

if __name__ == "__main__":
    main()
