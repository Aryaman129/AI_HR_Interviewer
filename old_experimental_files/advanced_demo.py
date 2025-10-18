"""
AI HR Interviewer - Advanced Version with Real AI
Full implementation with Ollama LLM integration and two-way conversation
"""

import streamlit as st
import json
import requests
import time
from datetime import datetime
from pathlib import Path
import sys

# Add backend to path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Try to import backend modules with better error handling
try:
    from backend.logic.resume_filter import ResumeFilter
    RESUME_FILTER_AVAILABLE = True
except ImportError as e:
    st.warning(f"Resume filter not available: {e}")
    RESUME_FILTER_AVAILABLE = False

try:
    from backend.logic.interview_engine import InterviewEngine
    INTERVIEW_ENGINE_AVAILABLE = True
except ImportError as e:
    st.warning(f"Interview engine not available: {e}")
    INTERVIEW_ENGINE_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="AI HR Interviewer - Advanced",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'resume_filter' not in st.session_state:
    try:
        st.session_state.resume_filter = ResumeFilter()
    except Exception as e:
        st.error(f"Failed to initialize resume filter: {e}")
        st.stop()

if 'candidates' not in st.session_state:
    st.session_state.candidates = []
if 'job_requirements' not in st.session_state:
    st.session_state.job_requirements = {}
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'interview_active' not in st.session_state:
    st.session_state.interview_active = False

class AdvancedInterviewEngine:
    """Advanced interview engine with real AI conversation"""

    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.model_name = "llama3:latest"
        self.conversation_context = []

    def check_ollama_connection(self):
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                return self.model_name in available_models, available_models
            return False, []
        except Exception as e:
            return False, str(e)

    def generate_ai_response(self, user_message, context=""):
        """Generate AI response using Ollama"""
        try:
            # Build conversation context
            system_prompt = """You are an experienced HR interviewer conducting a professional job interview.
            You should:
            1. Ask relevant follow-up questions based on the candidate's responses
            2. Allow the candidate to ask questions about the role, company, or interview process
            3. Maintain a professional but friendly tone
            4. Probe deeper into technical skills and experience when appropriate
            5. Answer candidate questions helpfully and honestly
            6. Keep responses concise but informative

            Remember: This is a two-way conversation. The candidate can ask you questions too."""

            prompt = f"{system_prompt}\n\nContext: {context}\n\nCandidate: {user_message}\n\nHR Interviewer:"

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 200
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()['response'].strip()
            else:
                return f"Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"AI Error: {str(e)}"

    def start_interview(self, candidate_info, job_requirements):
        """Start interview with AI-generated opening"""
        context = f"""
        Candidate: {candidate_info.get('filename', 'Unknown')}
        Role: {job_requirements.get('role', 'Position')}
        Required Skills: {', '.join(job_requirements.get('required_skills', []))}
        Experience Required: {job_requirements.get('min_experience_years', 0)} years
        """

        opening = self.generate_ai_response(
            "Hello, I'm ready to start the interview.",
            context + "\n\nPlease start the interview with a professional greeting and first question."
        )

        return opening

def main():
    st.title("🤖 AI HR Interviewer - Advanced Version")
    st.markdown("**Real AI-Powered Conversations with Ollama Integration**")

    # Initialize advanced engine
    if 'ai_engine' not in st.session_state:
        st.session_state.ai_engine = AdvancedInterviewEngine()

    # Check Ollama status
    with st.sidebar:
        st.header("🔧 AI Status")

        is_connected, models_or_error = st.session_state.ai_engine.check_ollama_connection()

        if is_connected:
            st.success("✅ Ollama Connected")
            st.success(f"✅ Model: {st.session_state.ai_engine.model_name}")
        else:
            st.error("❌ Ollama Not Connected")
            st.error(f"Available models: {models_or_error}")
            st.info("Please start Ollama: `ollama serve`")

        st.markdown("---")

        # Load sample data
        if st.button("📁 Load Sample Data"):
            load_sample_data()

        # Real resume filtering
        if st.button("🔍 Filter Real Resumes"):
            filter_real_resumes()

    # Main interface
    tab1, tab2, tab3 = st.tabs(["🎯 Dashboard", "💼 Job Setup", "🎤 AI Interview"])

    with tab1:
        show_advanced_dashboard()

    with tab2:
        show_job_setup()

    with tab3:
        show_ai_interview()

def load_sample_data():
    """Load sample data and process with real AI"""
    with st.spinner("Loading sample data..."):
        # Generate sample resumes if they don't exist
        from utils.resume_collector import ResumeCollector
        collector = ResumeCollector()
        collector.generate_sample_resumes()
        collector.create_job_requirements_samples()

        st.success("✅ Sample data loaded!")
        st.rerun()

def filter_real_resumes():
    """Filter resumes using real AI"""
    if not st.session_state.job_requirements:
        st.error("Please set job requirements first!")
        return

    with st.spinner("🤖 AI is analyzing resumes..."):
        try:
            # Use real resume filter with AI
            candidates = st.session_state.resume_filter.filter_resumes(
                st.session_state.job_requirements
            )
            st.session_state.candidates = candidates

            st.success(f"✅ AI analyzed {len(candidates)} candidates!")

            # Show top candidate
            if candidates:
                top = candidates[0]
                st.info(f"🏆 Top candidate: {top['filename']} ({top['match_score']}%)")

        except Exception as e:
            st.error(f"Error during AI analysis: {e}")

def show_advanced_dashboard():
    """Advanced dashboard with real AI insights"""
    st.header("📊 AI-Powered Dashboard")

    if not st.session_state.candidates:
        st.info("No candidates analyzed yet. Use the sidebar to load data and filter resumes.")
        return

    # Real AI metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🤖 AI Analyzed", len(st.session_state.candidates))

    with col2:
        high_match = len([c for c in st.session_state.candidates if c['match_score'] >= 80])
        st.metric("⭐ High Match", high_match)

    with col3:
        avg_score = sum(c['match_score'] for c in st.session_state.candidates) / len(st.session_state.candidates)
        st.metric("📈 Avg Score", f"{avg_score:.1f}%")

    with col4:
        interviews = len(st.session_state.conversation_history)
        st.metric("🎤 AI Interviews", interviews)

    # Candidate analysis
    st.subheader("🎯 AI Candidate Analysis")

    for candidate in st.session_state.candidates[:3]:
        with st.expander(f"📄 {candidate['filename']} - {candidate['match_score']}%"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**AI Extracted Skills:**")
                skills = candidate['parsed_info'].get('skills', [])
                st.write(", ".join(skills[:8]))

                st.write(f"**Experience:** {candidate['parsed_info'].get('experience_years', 0)} years")

            with col2:
                st.write(f"**AI Recommendation:** {candidate['recommendation']}")
                st.write(f"**Match Score:** {candidate['match_score']}%")

                if st.button(f"🎤 Interview {candidate['filename']}", key=f"interview_{candidate['filename']}"):
                    st.session_state.selected_candidate = candidate
                    st.session_state.interview_active = True
                    st.rerun()

def show_job_setup():
    """Job requirements setup"""
    st.header("💼 Job Requirements Setup")

    with st.form("job_form"):
        role = st.text_input("Job Role", value="Senior Software Engineer")

        required_skills = st.text_area(
            "Required Skills (comma-separated)",
            value="Python, JavaScript, React, AWS, Docker"
        )

        preferred_skills = st.text_area(
            "Preferred Skills (comma-separated)",
            value="Kubernetes, TypeScript, PostgreSQL"
        )

        min_exp = st.number_input("Minimum Experience (years)", 0, 20, 5)
        education = st.selectbox("Education Level", ["Bachelor", "Master", "PhD"])
        location = st.text_input("Location", value="Remote")

        if st.form_submit_button("💾 Save & Analyze"):
            st.session_state.job_requirements = {
                'role': role,
                'required_skills': [s.strip() for s in required_skills.split(',')],
                'preferred_skills': [s.strip() for s in preferred_skills.split(',')],
                'min_experience_years': min_exp,
                'education_level': education,
                'location': location
            }
            st.success("✅ Job requirements saved!")

def show_ai_interview():
    """AI-powered interview interface"""
    st.header("🎤 AI Interview Conductor")

    # Check AI status
    is_connected, _ = st.session_state.ai_engine.check_ollama_connection()

    if not is_connected:
        st.error("❌ AI not available. Please start Ollama: `ollama serve`")
        return

    if not st.session_state.interview_active:
        st.info("Select a candidate from the Dashboard to start an AI interview.")
        return

    candidate = st.session_state.get('selected_candidate')
    if not candidate:
        st.error("No candidate selected.")
        return

    st.success(f"🎤 AI Interview with: **{candidate['filename']}**")

    # Start interview if not started
    if not st.session_state.conversation_history:
        with st.spinner("🤖 AI is preparing the interview..."):
            opening = st.session_state.ai_engine.start_interview(
                candidate,
                st.session_state.job_requirements
            )

            st.session_state.conversation_history = [
                {"role": "ai", "message": opening, "timestamp": datetime.now()}
            ]

    # Display conversation
    st.subheader("💬 Conversation")

    for entry in st.session_state.conversation_history:
        if entry["role"] == "ai":
            st.markdown(f"**🤖 AI Interviewer:** {entry['message']}")
        else:
            st.markdown(f"**👤 Candidate:** {entry['message']}")
        st.markdown("---")

    # User input
    st.subheader("Your Response")
    user_input = st.text_area(
        "Type your response or question:",
        height=100,
        placeholder="You can answer the question or ask your own questions about the role, company, etc."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Send Response", type="primary"):
            if user_input.strip():
                # Add user message
                st.session_state.conversation_history.append({
                    "role": "user",
                    "message": user_input,
                    "timestamp": datetime.now()
                })

                # Generate AI response
                with st.spinner("🤖 AI is thinking..."):
                    context = f"Job: {st.session_state.job_requirements.get('role', '')}\n"
                    context += f"Candidate: {candidate['filename']}\n"
                    context += "Previous conversation:\n"

                    for entry in st.session_state.conversation_history[-3:]:
                        context += f"{entry['role']}: {entry['message']}\n"

                    ai_response = st.session_state.ai_engine.generate_ai_response(
                        user_input, context
                    )

                    st.session_state.conversation_history.append({
                        "role": "ai",
                        "message": ai_response,
                        "timestamp": datetime.now()
                    })

                st.rerun()

    with col2:
        if st.button("🎤 Voice Input"):
            st.info("Voice input coming soon!")

    with col3:
        if st.button("⏹️ End Interview"):
            st.session_state.interview_active = False
            st.session_state.selected_candidate = None
            st.success("Interview ended!")
            st.rerun()

if __name__ == "__main__":
    main()
