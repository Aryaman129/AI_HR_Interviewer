"""
AI HR Interviewer - Demo Version
Simplified demo without complex AI dependencies
"""

import streamlit as st
import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="AI HR Interviewer Demo",
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
        background-color: #ffffff;
        color: #000000;
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
if 'candidates' not in st.session_state:
    st.session_state.candidates = []
if 'current_interview' not in st.session_state:
    st.session_state.current_interview = None
if 'job_requirements' not in st.session_state:
    st.session_state.job_requirements = {}
if 'interview_log' not in st.session_state:
    st.session_state.interview_log = []

def load_sample_data():
    """Load sample resumes and job requirements"""
    # Sample candidates data
    sample_candidates = [
        {
            "filename": "John_Smith_Senior_Software_Engineer.txt",
            "match_score": 92.5,
            "recommendation": "Highly Recommended",
            "rank": 1,
            "parsed_info": {
                "skills": ["python", "java", "javascript", "react", "aws", "docker"],
                "experience_years": 8,
                "education": ["Bachelor of Science in Computer Science"]
            }
        },
        {
            "filename": "Sarah_Johnson_Cybersecurity_Specialist.txt",
            "match_score": 88.3,
            "recommendation": "Highly Recommended",
            "rank": 2,
            "parsed_info": {
                "skills": ["network security", "python", "linux", "siem", "incident response"],
                "experience_years": 5,
                "education": ["Bachelor of Science in Cybersecurity"]
            }
        },
        {
            "filename": "Mike_Chen_Data_Scientist.txt",
            "match_score": 76.8,
            "recommendation": "Recommended",
            "rank": 3,
            "parsed_info": {
                "skills": ["python", "machine learning", "sql", "tensorflow", "pandas"],
                "experience_years": 4,
                "education": ["Master of Science in Data Science"]
            }
        },
        {
            "filename": "Emily_Davis_Frontend_Developer.txt",
            "match_score": 65.2,
            "recommendation": "Consider",
            "rank": 4,
            "parsed_info": {
                "skills": ["javascript", "react", "html", "css", "typescript"],
                "experience_years": 3,
                "education": ["Bachelor of Science in Computer Science"]
            }
        },
        {
            "filename": "Robert_Wilson_DevOps_Engineer.txt",
            "match_score": 82.1,
            "recommendation": "Recommended",
            "rank": 5,
            "parsed_info": {
                "skills": ["aws", "docker", "kubernetes", "terraform", "jenkins"],
                "experience_years": 6,
                "education": ["Bachelor of Science in Information Technology"]
            }
        }
    ]

    # Sample job requirements
    sample_jobs = [
        {
            "role": "Senior Software Engineer",
            "required_skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
            "preferred_skills": ["Kubernetes", "TypeScript", "PostgreSQL", "Redis"],
            "min_experience_years": 5,
            "education_level": "Bachelor",
            "location": "Remote"
        },
        {
            "role": "Cybersecurity Specialist",
            "required_skills": ["Network Security", "SIEM", "Python", "Linux", "Incident Response"],
            "preferred_skills": ["CISSP", "CEH", "Penetration Testing", "Cloud Security"],
            "min_experience_years": 3,
            "education_level": "Bachelor",
            "location": "New York"
        }
    ]

    return sample_candidates, sample_jobs

def main():
    """Main application function"""

    # Header
    st.markdown('<h1 class="main-header">🤖 AI HR Interviewer Demo</h1>', unsafe_allow_html=True)
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
        if st.button("🔄 Load Sample Data"):
            candidates, jobs = load_sample_data()
            st.session_state.candidates = candidates
            st.session_state.job_requirements = jobs[0]  # Load first job as default
            st.success("✅ Sample data loaded!")
            st.rerun()

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

def show_dashboard():
    """Display main dashboard"""
    st.header("📊 Dashboard Overview")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_resumes = 5  # Sample data
        st.metric("📄 Total Resumes", total_resumes)

    with col2:
        total_candidates = len(st.session_state.candidates)
        st.metric("👥 Filtered Candidates", total_candidates)

    with col3:
        recommended = len([c for c in st.session_state.candidates if c.get('recommendation') == 'Highly Recommended'])
        st.metric("⭐ Highly Recommended", recommended)

    with col4:
        interviews_completed = len(st.session_state.interview_log)
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
            st.info("No candidates available. Click 'Load Sample Data' in the sidebar.")

    with col2:
        st.subheader("📈 Score Distribution")
        if st.session_state.candidates:
            scores = [c.get('match_score', 0) for c in st.session_state.candidates]
            df = pd.DataFrame({'Score': scores})
            st.bar_chart(df)
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

    # Sample resumes display
    st.subheader("📋 Sample Resumes Available")
    sample_resumes = [
        "John_Smith_Senior_Software_Engineer.txt",
        "Sarah_Johnson_Cybersecurity_Specialist.txt",
        "Mike_Chen_Data_Scientist.txt",
        "Emily_Davis_Frontend_Developer.txt",
        "Robert_Wilson_DevOps_Engineer.txt"
    ]

    for resume in sample_resumes:
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"📄 {resume}")

        with col2:
            st.write("Sample")

        with col3:
            st.write("✅ Ready")

def show_job_requirements():
    """Job requirements configuration interface"""
    st.header("💼 Job Requirements")

    # Job details form
    with st.form("job_requirements_form"):
        role = st.text_input("Job Role", value=st.session_state.job_requirements.get('role', 'Senior Software Engineer'))

        required_skills = st.text_area(
            "Required Skills (comma-separated)",
            value=', '.join(st.session_state.job_requirements.get('required_skills', ['Python', 'JavaScript', 'React']))
        )

        preferred_skills = st.text_area(
            "Preferred Skills (comma-separated)",
            value=', '.join(st.session_state.job_requirements.get('preferred_skills', ['AWS', 'Docker', 'Kubernetes']))
        )

        min_experience = st.number_input(
            "Minimum Experience (years)",
            min_value=0,
            max_value=20,
            value=st.session_state.job_requirements.get('min_experience_years', 5)
        )

        education_level = st.selectbox(
            "Education Level",
            ["High School", "Bachelor", "Master", "PhD"],
            index=1
        )

        location = st.text_input(
            "Location",
            value=st.session_state.job_requirements.get('location', 'Remote')
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
        if st.button("🔍 Filter Resumes", type="primary"):
            with st.spinner("Filtering resumes..."):
                time.sleep(2)  # Simulate processing
                candidates, _ = load_sample_data()
                st.session_state.candidates = candidates
                st.success(f"✅ Filtered {len(candidates)} candidates successfully!")
                st.rerun()

def show_interview_conductor():
    """Interview conductor interface"""
    st.header("🎤 Interview Conductor")

    if not st.session_state.candidates:
        st.warning("No candidates available. Please load sample data or filter resumes first.")
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

        if st.session_state.current_interview is None:
            if st.button("🚀 Start Interview", type="primary"):
                start_interview(selected_candidate)
        else:
            st.markdown(f"""
            <div class="interview-status status-active">
                <strong>Status:</strong> Active<br>
                <strong>Candidate:</strong> {st.session_state.current_interview['candidate']}<br>
                <strong>Questions:</strong> {len(st.session_state.interview_log)}
            </div>
            """, unsafe_allow_html=True)

            if st.button("⏹️ End Interview"):
                end_interview()

    # Interview interface
    if st.session_state.current_interview:
        show_interview_interface()

def start_interview(candidate):
    """Start a new interview"""
    st.session_state.current_interview = {
        'candidate': candidate['filename'],
        'start_time': datetime.now().isoformat(),
        'questions': [
            "What is your expected CTC (Cost to Company)?",
            "What is your reason for job change?",
            "Are you suitable to work at this location?",
            f"Can you elaborate on your experience with {candidate['parsed_info']['skills'][0]}?",
            "Describe your approach to debugging complex issues."
        ],
        'current_question': 0
    }
    st.session_state.interview_log = []
    st.success(f"✅ Interview started with {candidate['filename']}!")
    st.rerun()

def end_interview():
    """End current interview"""
    st.session_state.current_interview = None
    st.success("✅ Interview ended!")
    st.rerun()

def show_interview_interface():
    """Show the interview interface"""
    st.markdown("---")
    st.subheader("💬 Interview Session")

    interview = st.session_state.current_interview
    questions = interview['questions']
    current_q = interview['current_question']

    if current_q < len(questions):
        question = questions[current_q]
        st.markdown("**AI Interviewer:**")
        st.info(question)

        # Response input
        response = st.text_area("Your response:", height=100, key=f"response_{current_q}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Submit Response"):
                if response.strip():
                    # Add to log
                    st.session_state.interview_log.append({
                        'question': question,
                        'response': response,
                        'timestamp': datetime.now().isoformat()
                    })

                    # Move to next question
                    st.session_state.current_interview['current_question'] += 1
                    st.rerun()
                else:
                    st.warning("Please enter a response.")

        with col2:
            if st.button("🎤 Voice Response"):
                st.info("Voice recording feature coming soon!")
    else:
        st.success("🎉 Interview completed!")
        show_interview_summary()

def show_interview_summary():
    """Show interview summary"""
    st.subheader("📊 Interview Summary")

    if st.session_state.interview_log:
        st.write(f"**Candidate:** {st.session_state.current_interview['candidate']}")
        st.write(f"**Questions Answered:** {len(st.session_state.interview_log)}")

        # Calculate simple score
        total_words = sum(len(entry['response'].split()) for entry in st.session_state.interview_log)
        avg_words = total_words / len(st.session_state.interview_log)
        score = min(100, (avg_words / 50) * 100)

        st.metric("Overall Score", f"{score:.1f}%")

        # Show conversation
        with st.expander("📝 Full Conversation"):
            for i, entry in enumerate(st.session_state.interview_log):
                st.write(f"**Q{i+1}:** {entry['question']}")
                st.write(f"**A{i+1}:** {entry['response']}")
                st.write("---")

def show_analytics():
    """Analytics and reporting interface"""
    st.header("📈 Analytics & Reports")

    if not st.session_state.interview_log:
        st.info("No interview data available yet. Complete an interview to see analytics.")
        return

    # Analytics implementation
    st.subheader("📊 Interview Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Interviews", len(st.session_state.interview_log))

    with col2:
        if st.session_state.interview_log:
            avg_words = sum(len(entry['response'].split()) for entry in st.session_state.interview_log) / len(st.session_state.interview_log)
            st.metric("Avg Response Length", f"{avg_words:.1f} words")

    with col3:
        st.metric("Completion Rate", "100%")

    # Response analysis
    st.subheader("📝 Response Analysis")
    if st.session_state.interview_log:
        response_lengths = [len(entry['response'].split()) for entry in st.session_state.interview_log]
        df = pd.DataFrame({
            'Question': [f"Q{i+1}" for i in range(len(response_lengths))],
            'Response Length': response_lengths
        })
        st.bar_chart(df.set_index('Question'))

if __name__ == "__main__":
    main()
