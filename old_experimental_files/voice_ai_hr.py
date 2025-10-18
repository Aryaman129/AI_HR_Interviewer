"""
Voice-Enabled AI HR Interviewer
Complete system with speech recognition, text-to-speech, and AI conversation
"""

import streamlit as st
import json
import time
import threading
from datetime import datetime
from pathlib import Path
import sys

# Add current directory to path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Import voice engine
try:
    from voice_interview_engine import VoiceInterviewEngine
    VOICE_AVAILABLE = True
except ImportError as e:
    st.error(f"Voice engine not available: {e}")
    VOICE_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="🎤 Voice AI HR Interviewer",
    page_icon="🎤",
    layout="wide"
)

# Custom CSS for voice interface
st.markdown("""
<style>
    .voice-status {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
    }
    .listening { background-color: #ff6b6b; color: #000000; }
    .speaking { background-color: #4ecdc4; color: #000000; }
    .ready { background-color: #45b7d1; color: #000000; }
    .conversation-bubble {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 1rem;
        max-width: 80%;
        border: 1px solid #ddd;
    }
    .ai-bubble {
        background-color: #f0f8ff;
        margin-left: auto;
        border-bottom-right-radius: 0.3rem;
        color: #000000;
        border-left: 4px solid #1f77b4;
    }
    .user-bubble {
        background-color: #f8f0ff;
        margin-right: auto;
        border-bottom-left-radius: 0.3rem;
        color: #000000;
        border-right: 4px solid #9c27b0;
    }
    .voice-controls {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
    }
    .interview-header {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        color: #000000;
        margin-bottom: 1rem;
    }
    .candidate-info {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        color: #000000;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'voice_engine' not in st.session_state and VOICE_AVAILABLE:
    st.session_state.voice_engine = VoiceInterviewEngine()

if 'interview_active' not in st.session_state:
    st.session_state.interview_active = False

if 'voice_mode' not in st.session_state:
    st.session_state.voice_mode = False

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'candidates' not in st.session_state:
    st.session_state.candidates = []

if 'job_requirements' not in st.session_state:
    st.session_state.job_requirements = {}

def load_sample_candidates():
    """Load sample candidate data"""
    return [
        {
            "filename": "John_Smith_Senior_Software_Engineer.txt",
            "match_score": 92.5,
            "recommendation": "Highly Recommended",
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
            "parsed_info": {
                "skills": ["python", "machine learning", "sql", "tensorflow", "pandas"],
                "experience_years": 4,
                "education": ["Master of Science in Data Science"]
            }
        }
    ]

def main():
    st.title("🎤 Voice-Enabled AI HR Interviewer")
    st.markdown("**Real-time voice conversations with AI-powered interviews**")

    if not VOICE_AVAILABLE:
        st.error("❌ Voice engine not available. Please check dependencies.")
        return

    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Voice Controls")

        # Check AI status
        is_connected, models_or_error = st.session_state.voice_engine.check_ollama_connection()

        if is_connected:
            st.success("✅ AI Connected")
            st.success(f"✅ Model: {st.session_state.voice_engine.model_name}")
        else:
            st.error("❌ AI Not Connected")
            st.error("Please start Ollama: `ollama serve`")

        st.markdown("---")

        # Voice mode toggle
        voice_mode = st.toggle("🎤 Voice Mode", value=st.session_state.voice_mode)
        st.session_state.voice_mode = voice_mode

        if voice_mode:
            st.success("🎤 Voice mode enabled")
            st.info("Click 'Start Voice Interview' to begin")
        else:
            st.info("💬 Text mode enabled")

        st.markdown("---")

        # Load sample data
        if st.button("📁 Load Sample Data"):
            st.session_state.candidates = load_sample_candidates()
            st.session_state.job_requirements = {
                'role': 'Senior Software Engineer',
                'required_skills': ['Python', 'JavaScript', 'React', 'AWS'],
                'min_experience_years': 5
            }
            st.success("✅ Sample data loaded!")
            st.rerun()

    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Interview Setup", "🎤 Voice Interview", "📊 Results"])

    with tab1:
        show_interview_setup()

    with tab2:
        show_voice_interview()

    with tab3:
        show_interview_results()

def show_interview_setup():
    """Interview setup and candidate selection"""
    st.header("🎯 Interview Setup")

    # Job requirements
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💼 Job Requirements")
        with st.form("job_form"):
            role = st.text_input("Job Role", value=st.session_state.job_requirements.get('role', 'Senior Software Engineer'))
            required_skills = st.text_area("Required Skills", value=', '.join(st.session_state.job_requirements.get('required_skills', ['Python', 'JavaScript'])))
            min_exp = st.number_input("Min Experience (years)", value=st.session_state.job_requirements.get('min_experience_years', 5))

            if st.form_submit_button("💾 Save Requirements"):
                st.session_state.job_requirements = {
                    'role': role,
                    'required_skills': [s.strip() for s in required_skills.split(',')],
                    'min_experience_years': min_exp
                }
                st.success("✅ Requirements saved!")

    with col2:
        st.subheader("👥 Select Candidate")

        if not st.session_state.candidates:
            st.info("No candidates available. Load sample data from sidebar.")
        else:
            for i, candidate in enumerate(st.session_state.candidates):
                with st.expander(f"📄 {candidate['filename']} - {candidate['match_score']}%"):
                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.write(f"**Skills:** {', '.join(candidate['parsed_info']['skills'][:4])}")
                        st.write(f"**Experience:** {candidate['parsed_info']['experience_years']} years")

                    with col_b:
                        st.write(f"**Score:** {candidate['match_score']}%")
                        st.write(f"**Status:** {candidate['recommendation']}")

                    if st.button(f"🎤 Interview {candidate['filename']}", key=f"select_{i}"):
                        st.session_state.selected_candidate = candidate
                        st.session_state.interview_active = True

                        # Initialize interview
                        if VOICE_AVAILABLE:
                            opening = st.session_state.voice_engine.start_interview(
                                candidate, st.session_state.job_requirements
                            )
                            st.session_state.conversation_history = st.session_state.voice_engine.conversation_history

                        st.success(f"✅ Interview started with {candidate['filename']}")
                        st.rerun()

def show_voice_interview():
    """Voice interview interface"""
    st.header("🎤 Voice Interview Session")

    if not st.session_state.interview_active:
        st.info("No active interview. Please select a candidate from the Interview Setup tab.")
        return

    candidate = st.session_state.get('selected_candidate')
    if not candidate:
        st.error("No candidate selected.")
        return

    # Interview header
    st.markdown(f"""
    <div class="interview-header">
        <h3>🎤 Interviewing: {candidate['filename']}</h3>
        <p><strong>Match Score:</strong> {candidate.get('match_score', 'N/A')}% |
        <strong>Recommendation:</strong> {candidate.get('recommendation', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

    # Voice status indicator
    if st.session_state.voice_mode:
        st.markdown("""
        <div class="voice-status ready">
            🎤 Voice Mode Active - Ready for conversation
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="voice-status ready">
            💬 Text Mode Active
        </div>
        """, unsafe_allow_html=True)

    # Conversation display
    st.subheader("💬 Conversation")

    conversation_container = st.container()
    with conversation_container:
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
                        <strong>👤 Candidate:</strong><br>
                        {entry['message']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Conversation will appear here...")

    # Interview controls
    st.markdown("---")

    if st.session_state.voice_mode:
        # Voice mode controls
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎤 Start Voice Turn", type="primary", key="voice_turn"):
                conduct_voice_turn()

        with col2:
            if st.button("💬 Switch to Text", key="switch_text"):
                st.session_state.voice_mode = False
                st.rerun()

        with col3:
            if st.button("⏹️ End Interview", key="end_voice"):
                end_interview()

    else:
        # Text mode controls
        user_input = st.text_area("Your response:", height=100, key="text_input")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📤 Send Response", type="primary", key="send_text"):
                if user_input.strip():
                    process_text_response(user_input)

        with col2:
            if st.button("🎤 Switch to Voice", key="switch_voice"):
                st.session_state.voice_mode = True
                st.rerun()

        with col3:
            if st.button("⏹️ End Interview", key="end_text"):
                end_interview()

def conduct_voice_turn():
    """Conduct one turn of voice interview"""
    if not VOICE_AVAILABLE:
        st.error("Voice engine not available")
        return

    with st.spinner("🎤 Listening for your response..."):
        try:
            candidate_speech, ai_response = st.session_state.voice_engine.conduct_voice_interview_turn()

            # Update conversation history
            st.session_state.conversation_history = st.session_state.voice_engine.conversation_history

            if candidate_speech == "TIMEOUT":
                st.warning("⏰ No response detected. Please try again.")
            elif candidate_speech == "UNCLEAR":
                st.warning("🔇 Speech unclear. Please speak more clearly.")
            elif candidate_speech == "ERROR":
                st.error("❌ Audio error. Switching to text mode.")
                st.session_state.voice_mode = False
            else:
                st.success(f"✅ Heard: {candidate_speech}")

            st.rerun()

        except Exception as e:
            st.error(f"Voice processing error: {e}")

def process_text_response(user_input):
    """Process text response"""
    if not VOICE_AVAILABLE:
        st.error("Voice engine not available")
        return

    # Add user response
    st.session_state.voice_engine.conversation_history.append({
        'role': 'user',
        'message': user_input,
        'timestamp': datetime.now().isoformat()
    })

    # Generate AI response
    with st.spinner("🤖 AI is thinking..."):
        ai_response = st.session_state.voice_engine.generate_ai_response(user_input)

        st.session_state.voice_engine.conversation_history.append({
            'role': 'ai',
            'message': ai_response,
            'timestamp': datetime.now().isoformat()
        })

    # Update session state
    st.session_state.conversation_history = st.session_state.voice_engine.conversation_history

    st.rerun()

def end_interview():
    """End the current interview"""
    if VOICE_AVAILABLE and st.session_state.voice_engine:
        # Save interview log
        log_path = st.session_state.voice_engine.save_interview_log()
        st.success(f"✅ Interview ended. Log saved: {log_path}")

    st.session_state.interview_active = False
    st.session_state.selected_candidate = None
    st.rerun()

def show_interview_results():
    """Show interview results and analytics"""
    st.header("📊 Interview Results")

    if not st.session_state.conversation_history:
        st.info("No interview data available. Complete an interview to see results.")
        return

    if VOICE_AVAILABLE and st.session_state.voice_engine:
        summary = st.session_state.voice_engine.get_interview_summary()

        # Display summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Responses", summary.get('total_responses', 0))

        with col2:
            st.metric("Avg Response Length", f"{summary.get('avg_response_length', 0)} words")

        with col3:
            st.metric("Overall Score", f"{summary.get('scores', {}).get('overall', 0)}%")

        # Detailed scores
        st.subheader("📈 Detailed Scoring")
        scores = summary.get('scores', {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Communication", f"{scores.get('communication', 0)}%")
        with col2:
            st.metric("Engagement", f"{scores.get('engagement', 0)}%")

        # Recommendation
        recommendation = summary.get('recommendation', 'Unknown')
        if recommendation == 'Recommended':
            st.success(f"✅ **Recommendation:** {recommendation}")
        elif recommendation == 'Consider':
            st.warning(f"⚠️ **Recommendation:** {recommendation}")
        else:
            st.error(f"❌ **Recommendation:** {recommendation}")

    # Conversation analysis
    st.subheader("💬 Conversation Analysis")

    user_responses = [entry for entry in st.session_state.conversation_history if entry['role'] == 'user']
    ai_responses = [entry for entry in st.session_state.conversation_history if entry['role'] == 'ai']

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Total Exchanges:** {len(user_responses)}")
        st.write(f"**Interview Duration:** ~{len(st.session_state.conversation_history) * 2} minutes")

    with col2:
        if user_responses:
            avg_length = sum(len(r['message'].split()) for r in user_responses) / len(user_responses)
            st.write(f"**Avg Response Length:** {avg_length:.1f} words")
        st.write(f"**Mode Used:** {'Voice + Text' if st.session_state.voice_mode else 'Text Only'}")

if __name__ == "__main__":
    main()
