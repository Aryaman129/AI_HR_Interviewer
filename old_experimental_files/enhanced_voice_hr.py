"""
Enhanced Voice AI HR Interviewer
Advanced speech processing with multiple transcription models and robust error handling
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

# Import enhanced voice engine
try:
    from enhanced_voice_engine import EnhancedVoiceEngine
    ENHANCED_VOICE_AVAILABLE = True
except ImportError as e:
    st.error(f"Enhanced voice engine not available: {e}")
    ENHANCED_VOICE_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="🎤 Enhanced Voice AI HR",
    page_icon="🎤",
    layout="wide"
)

# Enhanced CSS for better visual feedback
st.markdown("""
<style>
    .voice-status {
        padding: 1rem;
        border-radius: 0.5rem;
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
    
    .conversation-bubble {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 1rem;
        max-width: 85%;
        border: 1px solid #ddd;
        position: relative;
    }
    
    .ai-bubble {
        background: linear-gradient(135deg, #f0f8ff, #e6f3ff);
        margin-left: auto;
        border-bottom-right-radius: 0.3rem;
        color: #000000;
        border-left: 4px solid #1f77b4;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #f8f0ff, #f0e6ff);
        margin-right: auto;
        border-bottom-left-radius: 0.3rem;
        color: #000000;
        border-right: 4px solid #9c27b0;
    }
    
    .confidence-indicator {
        position: absolute;
        top: 5px;
        right: 10px;
        font-size: 0.8em;
        opacity: 0.7;
    }
    
    .high-confidence { color: #28a745; }
    .medium-confidence { color: #ffc107; }
    .low-confidence { color: #dc3545; }
    
    .interview-metrics {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background-color: #28a745; }
    .status-inactive { background-color: #6c757d; }
    .status-error { background-color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'enhanced_voice_engine' not in st.session_state and ENHANCED_VOICE_AVAILABLE:
    st.session_state.enhanced_voice_engine = EnhancedVoiceEngine()

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

if 'voice_status' not in st.session_state:
    st.session_state.voice_status = {'is_listening': False, 'is_processing': False, 'is_speaking': False}

def load_sample_candidates():
    """Load enhanced sample candidate data"""
    return [
        {
            "filename": "John_Smith_Senior_Software_Engineer.txt",
            "match_score": 92.5,
            "recommendation": "Highly Recommended",
            "parsed_info": {
                "skills": ["python", "java", "javascript", "react", "aws", "docker", "kubernetes"],
                "experience_years": 8,
                "education": ["Bachelor of Science in Computer Science"]
            }
        },
        {
            "filename": "Sarah_Johnson_Cybersecurity_Specialist.txt", 
            "match_score": 88.3,
            "recommendation": "Highly Recommended",
            "parsed_info": {
                "skills": ["network security", "python", "linux", "siem", "incident response", "penetration testing"],
                "experience_years": 5,
                "education": ["Bachelor of Science in Cybersecurity", "CISSP Certified"]
            }
        },
        {
            "filename": "Mike_Chen_Data_Scientist.txt",
            "match_score": 76.8,
            "recommendation": "Recommended",
            "parsed_info": {
                "skills": ["python", "machine learning", "sql", "tensorflow", "pandas", "deep learning"],
                "experience_years": 4,
                "education": ["Master of Science in Data Science"]
            }
        }
    ]

def main():
    st.title("🎤 Enhanced Voice AI HR Interviewer")
    st.markdown("**Advanced speech processing with multiple transcription models**")
    
    if not ENHANCED_VOICE_AVAILABLE:
        st.error("❌ Enhanced voice engine not available. Please check dependencies.")
        return
    
    # Sidebar with enhanced controls
    with st.sidebar:
        st.header("🎛️ Enhanced Voice Controls")
        
        # AI Connection Status
        is_connected, models_or_error = st.session_state.enhanced_voice_engine.check_ollama_connection()
        
        col1, col2 = st.columns(2)
        with col1:
            if is_connected:
                st.markdown('<span class="status-indicator status-active"></span>**AI Connected**', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-indicator status-error"></span>**AI Disconnected**', unsafe_allow_html=True)
        
        with col2:
            if st.session_state.enhanced_voice_engine.whisper_available:
                st.markdown('<span class="status-indicator status-active"></span>**Whisper Ready**', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-indicator status-inactive"></span>**Whisper Unavailable**', unsafe_allow_html=True)
        
        if not is_connected:
            st.error("Please start Ollama: `ollama serve`")
        
        st.markdown("---")
        
        # Enhanced voice settings
        st.subheader("🎙️ Voice Settings")
        
        voice_mode = st.toggle("🎤 Enhanced Voice Mode", value=st.session_state.voice_mode)
        st.session_state.voice_mode = voice_mode
        
        if voice_mode:
            st.success("🎤 Enhanced voice mode enabled")
            
            # Voice processing options
            use_whisper = st.checkbox("Use Whisper STT", value=True, 
                                    disabled=not st.session_state.enhanced_voice_engine.whisper_available)
            
            confidence_threshold = st.slider("Confidence Threshold", 0.5, 1.0, 0.7, 0.1)
            
            listening_timeout = st.slider("Listening Timeout (seconds)", 15, 60, 30, 5)
            
        else:
            st.info("💬 Text mode enabled")
        
        st.markdown("---")
        
        # Quick actions
        if st.button("📁 Load Sample Data"):
            st.session_state.candidates = load_sample_candidates()
            st.session_state.job_requirements = {
                'role': 'Senior Software Engineer',
                'required_skills': ['Python', 'JavaScript', 'React', 'AWS'],
                'min_experience_years': 5
            }
            st.success("✅ Enhanced sample data loaded!")
            st.rerun()
    
    # Main interface
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Setup", "🎤 Enhanced Interview", "📊 Analytics", "🔧 Diagnostics"])
    
    with tab1:
        show_enhanced_setup()
    
    with tab2:
        show_enhanced_interview()
    
    with tab3:
        show_enhanced_analytics()
    
    with tab4:
        show_diagnostics()

def show_enhanced_setup():
    """Enhanced interview setup"""
    st.header("🎯 Enhanced Interview Setup")
    
    # Job requirements with validation
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💼 Job Requirements")
        with st.form("enhanced_job_form"):
            role = st.text_input("Job Role", value=st.session_state.job_requirements.get('role', 'Senior Software Engineer'))
            required_skills = st.text_area("Required Skills", value=', '.join(st.session_state.job_requirements.get('required_skills', ['Python', 'JavaScript'])))
            min_exp = st.number_input("Min Experience (years)", value=st.session_state.job_requirements.get('min_experience_years', 5))
            
            if st.form_submit_button("💾 Save Enhanced Requirements"):
                st.session_state.job_requirements = {
                    'role': role,
                    'required_skills': [s.strip() for s in required_skills.split(',')],
                    'min_experience_years': min_exp
                }
                st.success("✅ Enhanced requirements saved!")
    
    with col2:
        st.subheader("👥 Enhanced Candidate Selection")
        
        if not st.session_state.candidates:
            st.info("No candidates available. Load sample data from sidebar.")
        else:
            for i, candidate in enumerate(st.session_state.candidates):
                with st.expander(f"📄 {candidate['filename']} - {candidate['match_score']}%"):
                    
                    # Enhanced candidate display
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Skills:** {', '.join(candidate['parsed_info']['skills'][:5])}")
                        st.write(f"**Experience:** {candidate['parsed_info']['experience_years']} years")
                        st.write(f"**Education:** {', '.join(candidate['parsed_info']['education'])}")
                    
                    with col_b:
                        st.metric("Match Score", f"{candidate['match_score']}%")
                        st.write(f"**Status:** {candidate['recommendation']}")
                    
                    if st.button(f"🎤 Start Enhanced Interview", key=f"enhanced_select_{i}"):
                        start_enhanced_interview(candidate)

def start_enhanced_interview(candidate):
    """Start enhanced interview with better initialization"""
    st.session_state.selected_candidate = candidate
    st.session_state.interview_active = True
    
    # Initialize enhanced interview
    if ENHANCED_VOICE_AVAILABLE:
        opening = st.session_state.enhanced_voice_engine.start_interview(
            candidate, st.session_state.job_requirements
        )
        st.session_state.conversation_history = st.session_state.enhanced_voice_engine.conversation_history
    
    st.success(f"✅ Enhanced interview started with {candidate['filename']}")
    st.rerun()

def show_enhanced_interview():
    """Enhanced interview interface with real-time feedback"""
    st.header("🎤 Enhanced Voice Interview")
    
    if not st.session_state.interview_active:
        st.info("No active interview. Please select a candidate from the Setup tab.")
        return
    
    candidate = st.session_state.get('selected_candidate')
    if not candidate:
        st.error("No candidate selected.")
        return
    
    # Enhanced interview header with metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Candidate", candidate['filename'].replace('.txt', ''))
    with col2:
        st.metric("Match Score", f"{candidate['match_score']}%")
    with col3:
        exchanges = len([e for e in st.session_state.conversation_history if e['role'] == 'user'])
        st.metric("Exchanges", exchanges)
    
    # Real-time voice status
    if ENHANCED_VOICE_AVAILABLE:
        status = st.session_state.enhanced_voice_engine.get_listening_status()
        
        if status['is_listening']:
            st.markdown("""
            <div class="voice-status listening">
                🎤 LISTENING - Speak now...
            </div>
            """, unsafe_allow_html=True)
        elif status['is_processing']:
            st.markdown("""
            <div class="voice-status processing">
                🔄 PROCESSING - Analyzing speech...
            </div>
            """, unsafe_allow_html=True)
        elif status['is_speaking']:
            st.markdown("""
            <div class="voice-status speaking">
                🗣️ SPEAKING - AI is responding...
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="voice-status ready">
                ✅ READY - Click to start voice turn
            </div>
            """, unsafe_allow_html=True)
    
    # Enhanced conversation display
    st.subheader("💬 Enhanced Conversation")
    
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
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    confidence_class = "high-confidence" if confidence > 0.8 else "medium-confidence" if confidence > 0.6 else "low-confidence"
                    confidence_text = f"Confidence: {confidence:.1%}" if confidence < 1.0 else ""
                    
                    st.markdown(f"""
                    <div class="conversation-bubble user-bubble">
                        <div class="confidence-indicator {confidence_class}">{confidence_text}</div>
                        <strong>👤 Candidate:</strong><br>
                        {entry['message']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Enhanced conversation will appear here...")
    
    # Enhanced controls
    st.markdown("---")
    
    if st.session_state.voice_mode:
        # Enhanced voice controls
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🎤 Start Enhanced Voice Turn", type="primary", key="enhanced_voice_turn"):
                conduct_enhanced_voice_turn()
        
        with col2:
            if st.button("💬 Switch to Text", key="switch_to_text"):
                st.session_state.voice_mode = False
                st.rerun()
        
        with col3:
            if st.button("⏸️ Pause Interview", key="pause_interview"):
                st.info("Interview paused. Click 'Start Enhanced Voice Turn' to continue.")
        
        with col4:
            if st.button("⏹️ End Interview", key="end_enhanced_interview"):
                end_enhanced_interview()
    
    else:
        # Enhanced text controls
        user_input = st.text_area("Your response:", height=100, key="enhanced_text_input")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Send Response", type="primary", key="send_enhanced_text"):
                if user_input.strip():
                    process_enhanced_text_response(user_input)
        
        with col2:
            if st.button("🎤 Switch to Voice", key="switch_to_voice"):
                st.session_state.voice_mode = True
                st.rerun()
        
        with col3:
            if st.button("⏹️ End Interview", key="end_enhanced_text"):
                end_enhanced_interview()

def conduct_enhanced_voice_turn():
    """Conduct enhanced voice interview turn"""
    if not ENHANCED_VOICE_AVAILABLE:
        st.error("Enhanced voice engine not available")
        return
    
    with st.spinner("🎤 Enhanced voice processing..."):
        try:
            candidate_speech, ai_response, turn_info = st.session_state.enhanced_voice_engine.conduct_enhanced_voice_turn()
            
            # Update conversation history
            st.session_state.conversation_history = st.session_state.enhanced_voice_engine.conversation_history
            
            # Show detailed feedback
            if turn_info['status'] == 'success':
                st.success(f"✅ Voice turn completed! Confidence: {turn_info['confidence']:.1%}")
            elif turn_info['status'] == 'timeout':
                st.warning("⏰ No response detected. Please try again.")
            elif turn_info['status'] == 'unclear':
                st.warning("🔇 Speech unclear. Please speak more clearly.")
            else:
                st.error("❌ Audio error occurred.")
            
            # Show processing metrics
            if turn_info['listening_duration'] > 0:
                st.info(f"Listening: {turn_info['listening_duration']:.1f}s | Processing: {turn_info['processing_duration']:.1f}s")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Enhanced voice processing error: {e}")

def process_enhanced_text_response(user_input):
    """Process enhanced text response"""
    if not ENHANCED_VOICE_AVAILABLE:
        st.error("Enhanced voice engine not available")
        return
    
    # Add user response with high confidence (text input)
    st.session_state.enhanced_voice_engine.conversation_history.append({
        'role': 'user',
        'message': user_input,
        'timestamp': datetime.now().isoformat(),
        'confidence': 1.0
    })
    
    # Generate AI response
    with st.spinner("🤖 Enhanced AI processing..."):
        ai_response = st.session_state.enhanced_voice_engine.generate_ai_response_with_retry(user_input)
        
        st.session_state.enhanced_voice_engine.conversation_history.append({
            'role': 'ai',
            'message': ai_response,
            'timestamp': datetime.now().isoformat(),
            'confidence': 1.0
        })
    
    # Update session state
    st.session_state.conversation_history = st.session_state.enhanced_voice_engine.conversation_history
    
    st.rerun()

def end_enhanced_interview():
    """End enhanced interview with detailed logging"""
    if ENHANCED_VOICE_AVAILABLE and st.session_state.enhanced_voice_engine:
        # Save enhanced interview log
        log_path = st.session_state.enhanced_voice_engine.save_interview_log()
        st.success(f"✅ Enhanced interview ended. Detailed log saved: {log_path}")
    
    st.session_state.interview_active = False
    st.session_state.selected_candidate = None
    st.rerun()

def show_enhanced_analytics():
    """Enhanced analytics with detailed metrics"""
    st.header("📊 Enhanced Analytics")
    
    if not st.session_state.conversation_history:
        st.info("No interview data available. Complete an interview to see enhanced analytics.")
        return
    
    # Enhanced metrics
    user_responses = [entry for entry in st.session_state.conversation_history if entry['role'] == 'user']
    
    if user_responses:
        # Confidence analysis
        confidences = [entry.get('confidence', 1.0) for entry in user_responses]
        avg_confidence = sum(confidences) / len(confidences)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Responses", len(user_responses))
        with col2:
            avg_length = sum(len(r['message'].split()) for r in user_responses) / len(user_responses)
            st.metric("Avg Response Length", f"{avg_length:.1f} words")
        with col3:
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        with col4:
            duration = len(st.session_state.conversation_history) * 1.5
            st.metric("Est. Duration", f"{duration:.1f} min")
        
        # Confidence distribution
        st.subheader("🎯 Confidence Analysis")
        high_conf = len([c for c in confidences if c > 0.8])
        medium_conf = len([c for c in confidences if 0.6 <= c <= 0.8])
        low_conf = len([c for c in confidences if c < 0.6])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("High Confidence", f"{high_conf}/{len(confidences)}")
        with col2:
            st.metric("Medium Confidence", f"{medium_conf}/{len(confidences)}")
        with col3:
            st.metric("Low Confidence", f"{low_conf}/{len(confidences)}")

def show_diagnostics():
    """Enhanced diagnostics and system status"""
    st.header("🔧 Enhanced Diagnostics")
    
    if ENHANCED_VOICE_AVAILABLE:
        engine = st.session_state.enhanced_voice_engine
        
        # System status
        st.subheader("🖥️ System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Speech Recognition:**")
            st.write(f"- Google STT: ✅ Available")
            st.write(f"- Whisper STT: {'✅ Available' if engine.whisper_available else '❌ Not Available'}")
            st.write(f"- Sample Rate: {engine.sample_rate} Hz")
            st.write(f"- Energy Threshold: {engine.recognizer.energy_threshold}")
        
        with col2:
            st.write("**Voice Processing:**")
            st.write(f"- Listening Timeout: {engine.listening_timeout}s")
            st.write(f"- Phrase Time Limit: {engine.phrase_time_limit}s")
            st.write(f"- Pause Threshold: {engine.pause_threshold}s")
            st.write(f"- Min Confidence: {engine.min_confidence}")
        
        # Test microphone
        if st.button("🎤 Test Microphone"):
            with st.spinner("Testing microphone..."):
                try:
                    test_result, confidence = engine.advanced_listen_for_speech(timeout=5)
                    if test_result not in ["TIMEOUT", "ERROR", "UNCLEAR"]:
                        st.success(f"✅ Microphone test successful! Heard: '{test_result}' (Confidence: {confidence:.1%})")
                    else:
                        st.warning(f"⚠️ Microphone test result: {test_result}")
                except Exception as e:
                    st.error(f"❌ Microphone test failed: {e}")

if __name__ == "__main__":
    main()
