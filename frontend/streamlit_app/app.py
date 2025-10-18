"""
AI HR Interviewer - Streamlit Dashboard
Main application interface for the AI HR system
"""

import streamlit as st
import json
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from backend.logic.resume_filter import ResumeFilter
    from backend.logic.interview_engine import InterviewEngine
    from utils.resume_collector import ResumeCollector
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please make sure you're running from the project root directory and all dependencies are installed.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="AI HR Interviewer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .candidate-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #808080;
    }
    .interview-status {
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .status-active { background-color: #d4edda; color: #155724; }
    .status-pending { background-color: #fff3cd; color: #856404; }
    .status-completed { background-color: #d1ecf1; color: #0c5460; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'resume_filter' not in st.session_state:
    st.session_state.resume_filter = ResumeFilter()
if 'interview_engine' not in st.session_state:
    st.session_state.interview_engine = InterviewEngine()
if 'candidates' not in st.session_state:
    st.session_state.candidates = []
if 'current_interview' not in st.session_state:
    st.session_state.current_interview = None
if 'job_requirements' not in st.session_state:
    st.session_state.job_requirements = {}

def main():
    """Main application function"""

    # Header
    st.markdown('<h1 class="main-header">🤖 AI HR Interviewer</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["Dashboard", "Resume Management", "Job Requirements", "Interview Conductor", "Analytics"]
        )

        st.markdown("---")
        st.markdown("### Quick Actions")
        if st.button("🔄 Refresh Data"):
            st.rerun()

        if st.button("📁 Generate Sample Data"):
            generate_sample_data()

    # Route to selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Resume Management":
        show_resume_management()
    elif page == "Job Requirements":
        show_job_requirements()
    elif page == "Interview Conductor":
        show_interview_conductor()
    elif page == "Analytics":
        show_analytics()

def generate_sample_data():
    """Generate sample resumes and job requirements"""
    with st.spinner("Generating sample data..."):
        collector = ResumeCollector()
        resumes = collector.generate_sample_resumes()
        jobs = collector.create_job_requirements_samples()

        st.success(f"✅ Generated {len(resumes)} sample resumes and {len(jobs)} job requirements!")
        st.rerun()

def show_dashboard():
    """Display main dashboard"""
    st.header("📊 Dashboard Overview")

    # Load existing candidates if available
    candidates_file = Path("frontend/streamlit_app/candidates.json")
    if candidates_file.exists():
        with open(candidates_file, 'r') as f:
            st.session_state.candidates = json.load(f)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_resumes = len(list(Path("backend/data/resumes").glob("*"))) if Path("backend/data/resumes").exists() else 0
        st.metric("📄 Total Resumes", total_resumes)

    with col2:
        total_candidates = len(st.session_state.candidates)
        st.metric("👥 Filtered Candidates", total_candidates)

    with col3:
        recommended = len([c for c in st.session_state.candidates if c.get('recommendation') == 'Highly Recommended'])
        st.metric("⭐ Highly Recommended", recommended)

    with col4:
        interviews_completed = len(list(Path("frontend/chat_logs").glob("*.json"))) if Path("frontend/chat_logs").exists() else 0
        st.metric("✅ Interviews Completed", interviews_completed)

    st.markdown("---")

    # Recent activity
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Top Candidates")
        if st.session_state.candidates:
            top_candidates = sorted(st.session_state.candidates, key=lambda x: x.get('match_score', 0), reverse=True)[:5]
            for candidate in top_candidates:
                with st.container():
                    st.markdown(f"""
                    <div class="candidate-card">
                        <strong>{candidate['filename']}</strong><br>
                        Match Score: {candidate.get('match_score', 0)}%<br>
                        Recommendation: {candidate.get('recommendation', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No candidates filtered yet. Please set job requirements and filter resumes.")

    with col2:
        st.subheader("📈 Score Distribution")
        if st.session_state.candidates:
            scores = [c.get('match_score', 0) for c in st.session_state.candidates]
            fig = px.histogram(x=scores, nbins=10, title="Candidate Score Distribution")
            fig.update_layout(xaxis_title="Match Score", yaxis_title="Number of Candidates")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for visualization.")

def show_resume_management():
    """Resume upload and management interface"""
    st.header("📁 Resume Management")

    # File upload section
    st.subheader("Upload Resumes")
    uploaded_files = st.file_uploader(
        "Choose resume files",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files"
    )

    if uploaded_files:
        resumes_dir = Path("backend/data/resumes")
        resumes_dir.mkdir(parents=True, exist_ok=True)

        for uploaded_file in uploaded_files:
            file_path = resumes_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        st.success(f"✅ Uploaded {len(uploaded_files)} resume(s) successfully!")

    st.markdown("---")

    # Existing resumes
    st.subheader("📋 Existing Resumes")
    resumes_dir = Path("backend/data/resumes")

    if resumes_dir.exists():
        resume_files = list(resumes_dir.glob("*"))
        if resume_files:
            for file_path in resume_files:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(f"📄 {file_path.name}")

                with col2:
                    file_size = file_path.stat().st_size / 1024  # KB
                    st.write(f"{file_size:.1f} KB")

                with col3:
                    if st.button("🗑️", key=f"delete_{file_path.name}"):
                        file_path.unlink()
                        st.rerun()
        else:
            st.info("No resumes uploaded yet.")
    else:
        st.info("Resume directory not found. Upload some resumes to get started.")

def show_job_requirements():
    """Job requirements configuration interface"""
    st.header("💼 Job Requirements")

    # Load sample jobs if available
    sample_jobs_file = Path("config/sample_jobs.json")
    sample_jobs = []
    if sample_jobs_file.exists():
        with open(sample_jobs_file, 'r') as f:
            sample_jobs = json.load(f)

    # Job selection or custom input
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Use Sample Job")
        if sample_jobs:
            selected_job = st.selectbox(
                "Select a sample job:",
                options=["Custom"] + [job['role'] for job in sample_jobs]
            )

            if selected_job != "Custom":
                job_data = next(job for job in sample_jobs if job['role'] == selected_job)
                st.session_state.job_requirements = job_data
                st.json(job_data)
        else:
            st.info("No sample jobs available. Create custom requirements.")

    with col2:
        st.subheader("✏️ Custom Job Requirements")

        # Job details form
        with st.form("job_requirements_form"):
            role = st.text_input("Job Role", value=st.session_state.job_requirements.get('role', ''))

            required_skills = st.text_area(
                "Required Skills (comma-separated)",
                value=', '.join(st.session_state.job_requirements.get('required_skills', []))
            )

            preferred_skills = st.text_area(
                "Preferred Skills (comma-separated)",
                value=', '.join(st.session_state.job_requirements.get('preferred_skills', []))
            )

            min_experience = st.number_input(
                "Minimum Experience (years)",
                min_value=0,
                max_value=20,
                value=st.session_state.job_requirements.get('min_experience_years', 0)
            )

            education_level = st.selectbox(
                "Education Level",
                ["High School", "Bachelor", "Master", "PhD"],
                index=["High School", "Bachelor", "Master", "PhD"].index(
                    st.session_state.job_requirements.get('education_level', 'Bachelor')
                )
            )

            location = st.text_input(
                "Location",
                value=st.session_state.job_requirements.get('location', '')
            )

            submitted = st.form_submit_button("💾 Save Requirements")

            if submitted:
                st.session_state.job_requirements = {
                    'role': role,
                    'required_skills': [skill.strip() for skill in required_skills.split(',') if skill.strip()],
                    'preferred_skills': [skill.strip() for skill in preferred_skills.split(',') if skill.strip()],
                    'min_experience_years': min_experience,
                    'education_level': education_level,
                    'location': location
                }
                st.success("✅ Job requirements saved!")

    st.markdown("---")

    # Filter resumes button
    if st.session_state.job_requirements:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Filter Resumes", type="primary"):
                filter_resumes()

        with col2:
            st.metric("Current Job Role", st.session_state.job_requirements.get('role', 'Not Set'))

def filter_resumes():
    """Filter resumes based on job requirements"""
    if not st.session_state.job_requirements:
        st.error("Please set job requirements first!")
        return

    with st.spinner("Filtering resumes..."):
        try:
            candidates = st.session_state.resume_filter.filter_resumes(st.session_state.job_requirements)
            st.session_state.candidates = candidates

            # Save results
            st.session_state.resume_filter.save_filtered_results(candidates)

            st.success(f"✅ Filtered {len(candidates)} candidates successfully!")

            # Show quick preview
            if candidates:
                st.subheader("🎯 Top 3 Candidates")
                for i, candidate in enumerate(candidates[:3]):
                    st.write(f"{i+1}. **{candidate['filename']}** - Score: {candidate['match_score']}% ({candidate['recommendation']})")

        except Exception as e:
            st.error(f"Error filtering resumes: {str(e)}")

def show_interview_conductor():
    """Interview conductor interface"""
    st.header("🎤 Interview Conductor")

    # Load candidates
    if not st.session_state.candidates:
        candidates_file = Path("frontend/streamlit_app/candidates.json")
        if candidates_file.exists():
            with open(candidates_file, 'r') as f:
                st.session_state.candidates = json.load(f)

    if not st.session_state.candidates:
        st.warning("No candidates available. Please filter resumes first.")
        return

    # Candidate selection
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("👥 Select Candidate")
        candidate_options = [f"{c['filename']} (Score: {c['match_score']}%)" for c in st.session_state.candidates]
        selected_idx = st.selectbox("Choose candidate to interview:", range(len(candidate_options)), format_func=lambda x: candidate_options[x])

        selected_candidate = st.session_state.candidates[selected_idx]

        # Candidate details
        with st.expander("📋 Candidate Details"):
            st.write(f"**File:** {selected_candidate['filename']}")
            st.write(f"**Match Score:** {selected_candidate['match_score']}%")
            st.write(f"**Recommendation:** {selected_candidate['recommendation']}")

            if 'parsed_info' in selected_candidate:
                info = selected_candidate['parsed_info']
                st.write(f"**Experience:** {info.get('experience_years', 'N/A')} years")
                st.write(f"**Skills:** {', '.join(info.get('skills', [])[:5])}")

    with col2:
        st.subheader("🎮 Interview Controls")

        # Interview status
        interview_status = st.session_state.interview_engine.get_interview_status()

        if interview_status['status'] == 'no_active_interview':
            if st.button("🚀 Start Interview", type="primary"):
                start_interview(selected_candidate)
        else:
            st.markdown(f"""
            <div class="interview-status status-{interview_status['status']}">
                <strong>Status:</strong> {interview_status['status'].title()}<br>
                <strong>Progress:</strong> {interview_status.get('progress', 'N/A')}<br>
                <strong>Duration:</strong> {interview_status.get('duration', 'N/A')}
            </div>
            """, unsafe_allow_html=True)

            if st.button("⏹️ End Interview"):
                end_interview()

    # Interview interface
    if st.session_state.current_interview:
        show_interview_interface()

def start_interview(candidate):
    """Start a new interview"""
    try:
        interview_id = st.session_state.interview_engine.start_interview(
            candidate,
            st.session_state.job_requirements
        )
        st.session_state.current_interview = interview_id
        st.success(f"✅ Interview started! ID: {interview_id}")
        st.rerun()
    except Exception as e:
        st.error(f"Error starting interview: {str(e)}")

def end_interview():
    """End current interview"""
    st.session_state.current_interview = None
    st.success("✅ Interview ended!")
    st.rerun()

def show_interview_interface():
    """Show the interview interface"""
    st.markdown("---")
    st.subheader("💬 Interview Session")

    # Get next question
    next_question = st.session_state.interview_engine.get_next_question()

    if next_question:
        st.markdown("**AI Interviewer:**")
        st.info(next_question)

        # Response input
        response = st.text_area("Your response:", height=100, key="interview_response")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Submit Response"):
                if response.strip():
                    process_interview_response(response)
                else:
                    st.warning("Please enter a response.")

        with col2:
            if st.button("🎤 Voice Response"):
                st.info("Voice recording feature coming soon!")
    else:
        st.success("🎉 Interview completed!")
        show_interview_summary()

def process_interview_response(response):
    """Process interview response"""
    try:
        result = st.session_state.interview_engine.process_response(response)

        if result.get('type') == 'complete':
            st.success("Interview completed!")
            st.session_state.current_interview = None

        st.rerun()
    except Exception as e:
        st.error(f"Error processing response: {str(e)}")

def show_interview_summary():
    """Show interview summary"""
    st.subheader("📊 Interview Summary")
    # Implementation for showing interview results
    st.info("Interview summary will be displayed here.")

def show_analytics():
    """Analytics and reporting interface"""
    st.header("📈 Analytics & Reports")

    # Load interview logs
    logs_dir = Path("frontend/chat_logs")
    if not logs_dir.exists() or not list(logs_dir.glob("*.json")):
        st.info("No interview data available yet.")
        return

    # Analytics implementation
    st.subheader("📊 Interview Statistics")

    # Placeholder for analytics
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Interviews", len(list(logs_dir.glob("*.json"))))

    with col2:
        st.metric("Average Score", "75.2%")

    st.info("Detailed analytics coming soon!")

if __name__ == "__main__":
    main()
