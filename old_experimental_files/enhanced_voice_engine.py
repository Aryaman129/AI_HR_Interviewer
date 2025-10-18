"""
Enhanced Voice Interview Engine with Advanced Speech Processing
Addresses speech recognition smoothness, message processing reliability, and transcription accuracy
"""

import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import queue
import time
import json
import requests
import whisper
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple
# import webrtcvad  # Optional - for advanced VAD
import collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedVoiceEngine:
    """Advanced voice processing with multiple transcription models and robust error handling"""

    def __init__(self):
        # Initialize multiple speech recognition systems
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Initialize local Whisper model for better accuracy
        try:
            self.whisper_model = whisper.load_model("base")
            self.whisper_available = True
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.warning(f"Whisper not available: {e}")
            self.whisper_available = False

        # Initialize TTS with enhanced settings
        self.tts_engine = pyttsx3.init()
        self._setup_enhanced_tts()

        # Voice Activity Detection (optional)
        # self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2 (0-3)

        # Audio processing settings
        self.sample_rate = 16000  # Optimal for speech recognition
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)

        # Enhanced listening parameters
        self.listening_timeout = 30  # Extended timeout for longer responses
        self.phrase_time_limit = 60  # Allow up to 1 minute responses
        self.pause_threshold = 1.5   # Longer pause detection
        self.energy_threshold = 300  # Adjusted for better noise handling

        # Audio buffers and queues
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False

        # Transcription confidence tracking
        self.transcription_confidence = 0.0
        self.min_confidence = 0.7

        # Ollama configuration
        self.ollama_url = "http://localhost:11434"
        self.model_name = "llama3:latest"

        # Interview state
        self.conversation_history = []
        self.current_candidate = None
        self.job_requirements = None

        # Enhanced microphone calibration
        self._enhanced_microphone_setup()

    def _setup_enhanced_tts(self):
        """Configure TTS with enhanced settings for natural speech"""
        voices = self.tts_engine.getProperty('voices')

        # Select the best available voice
        preferred_voices = ['zira', 'hazel', 'female']
        selected_voice = None

        for voice in voices:
            voice_name = voice.name.lower()
            if any(pref in voice_name for pref in preferred_voices):
                selected_voice = voice.id
                break

        if selected_voice:
            self.tts_engine.setProperty('voice', selected_voice)

        # Optimize speech parameters
        self.tts_engine.setProperty('rate', 175)    # Slightly slower for clarity
        self.tts_engine.setProperty('volume', 0.85) # Comfortable volume

    def _enhanced_microphone_setup(self):
        """Enhanced microphone calibration with noise profiling"""
        try:
            with self.microphone as source:
                logger.info("Performing enhanced microphone calibration...")

                # Extended calibration for better noise profiling
                self.recognizer.adjust_for_ambient_noise(source, duration=2)

                # Set optimized recognition parameters
                self.recognizer.energy_threshold = self.energy_threshold
                self.recognizer.pause_threshold = self.pause_threshold
                self.recognizer.phrase_threshold = 0.3
                self.recognizer.non_speaking_duration = 0.8

                logger.info(f"Microphone calibrated - Energy threshold: {self.recognizer.energy_threshold}")

        except Exception as e:
            logger.error(f"Enhanced microphone setup failed: {e}")

    def check_ollama_connection(self):
        """Check Ollama connection with enhanced error handling"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                return self.model_name in available_models, available_models
            return False, []
        except Exception as e:
            return False, str(e)

    def enhanced_speech_recognition(self, audio_data) -> Tuple[str, float]:
        """Multi-model speech recognition with confidence scoring"""
        results = []

        # Method 1: Google Speech Recognition
        try:
            google_result = self.recognizer.recognize_google(audio_data)
            if google_result:
                results.append(("google", google_result, 0.8))  # Default confidence
                logger.info(f"Google STT: {google_result}")
        except Exception as e:
            logger.warning(f"Google STT failed: {e}")

        # Method 2: Whisper (if available)
        if self.whisper_available:
            try:
                # Convert audio to format Whisper expects
                audio_np = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
                whisper_result = self.whisper_model.transcribe(audio_np)

                if whisper_result and whisper_result['text'].strip():
                    confidence = whisper_result.get('confidence', 0.9)
                    results.append(("whisper", whisper_result['text'].strip(), confidence))
                    logger.info(f"Whisper STT: {whisper_result['text']} (confidence: {confidence})")

            except Exception as e:
                logger.warning(f"Whisper STT failed: {e}")

        # Select best result based on confidence and length
        if not results:
            return "UNCLEAR", 0.0

        # Prefer Whisper if confidence is high, otherwise use Google
        best_result = max(results, key=lambda x: x[2] * len(x[1].split()))

        return best_result[1], best_result[2]

    def advanced_listen_for_speech(self, timeout=30) -> Tuple[str, float]:
        """Advanced speech listening with voice activity detection and buffering"""
        self.is_listening = True

        try:
            with self.microphone as source:
                logger.info("🎤 Advanced listening started...")

                # Dynamic noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Listen with extended parameters
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=self.phrase_time_limit
                )

                logger.info("🔄 Processing speech with multiple models...")
                self.is_processing = True

                # Use enhanced recognition
                text, confidence = self.enhanced_speech_recognition(audio)

                if confidence < self.min_confidence and text != "UNCLEAR":
                    logger.warning(f"Low confidence transcription: {confidence}")
                    return "UNCLEAR", confidence

                logger.info(f"✅ Recognized: {text} (confidence: {confidence})")
                return text, confidence

        except sr.WaitTimeoutError:
            logger.info("⏰ Listening timeout")
            return "TIMEOUT", 0.0
        except sr.UnknownValueError:
            logger.warning("🔇 Speech unclear")
            return "UNCLEAR", 0.0
        except sr.RequestError as e:
            logger.error(f"❌ Speech recognition error: {e}")
            return "ERROR", 0.0
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return "ERROR", 0.0
        finally:
            self.is_listening = False
            self.is_processing = False

    def speak_with_feedback(self, text: str):
        """Enhanced TTS with visual feedback and interruption capability"""
        if self.is_speaking:
            return

        self.is_speaking = True
        try:
            logger.info(f"🗣️ AI Speaking: {text}")

            # Split long responses for better pacing
            sentences = text.split('. ')
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                if i > 0:
                    sentence = sentence.strip()
                if not sentence.endswith('.') and i < len(sentences) - 1:
                    sentence += '.'

                self.tts_engine.say(sentence)
                self.tts_engine.runAndWait()

                # Brief pause between sentences
                if i < len(sentences) - 1:
                    time.sleep(0.3)

        except Exception as e:
            logger.error(f"❌ TTS Error: {e}")
        finally:
            self.is_speaking = False

    def generate_ai_response_with_retry(self, user_message: str, context: str = "") -> str:
        """Generate AI response with retry logic and timeout handling"""
        max_retries = 3
        base_timeout = 60

        for attempt in range(max_retries):
            try:
                timeout = base_timeout + (attempt * 30)  # Increase timeout with retries

                system_prompt = f"""You are an experienced HR interviewer conducting a professional job interview.

Current Context:
- Candidate: {self.current_candidate.get('filename', 'Unknown') if self.current_candidate else 'Unknown'}
- Role: {self.job_requirements.get('role', 'Position') if self.job_requirements else 'Position'}
- Required Skills: {', '.join(self.job_requirements.get('required_skills', [])) if self.job_requirements else 'Various'}

Interview Guidelines:
1. Ask relevant follow-up questions based on candidate responses
2. Allow candidates to ask questions about the role, company, benefits, team, etc.
3. Maintain a professional but friendly conversational tone
4. Probe deeper into technical skills and experience when appropriate
5. Answer candidate questions helpfully and provide realistic information
6. Keep responses concise but informative (1-2 sentences max for voice)
7. Show genuine interest in the candidate's background and motivations

Remember: This is a voice conversation, so keep responses brief and natural."""

                # Add conversation history
                conversation_context = ""
                if self.conversation_history:
                    conversation_context = "\n\nRecent conversation:\n"
                    for entry in self.conversation_history[-2:]:  # Last 2 exchanges
                        role = "Interviewer" if entry['role'] == 'ai' else "Candidate"
                        conversation_context += f"{role}: {entry['message']}\n"

                prompt = f"{system_prompt}{conversation_context}\n\nCandidate just said: \"{user_message}\"\n\nYour brief response:"

                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 80,  # Shorter for voice responses
                            "top_p": 0.9,
                            "num_ctx": 1024    # Reduced context for faster processing
                        }
                    },
                    timeout=timeout
                )

                if response.status_code == 200:
                    ai_response = response.json()['response'].strip()
                    # Clean up response
                    if ai_response.startswith('"') and ai_response.endswith('"'):
                        ai_response = ai_response[1:-1]

                    # Ensure response is concise for voice
                    sentences = ai_response.split('. ')
                    if len(sentences) > 2:
                        ai_response = '. '.join(sentences[:2]) + '.'

                    return ai_response
                else:
                    logger.warning(f"Ollama returned status {response.status_code}, attempt {attempt + 1}")

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"AI generation error on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        # Fallback responses
        fallback_responses = [
            "I understand. Could you tell me more about that?",
            "That's interesting. What else would you like to share?",
            "Thank you for that response. Do you have any questions for me?",
            "I see. Let's continue with the next topic."
        ]

        return fallback_responses[len(self.conversation_history) % len(fallback_responses)]

    def start_interview(self, candidate_info: Dict, job_requirements: Dict) -> str:
        """Start enhanced interview session"""
        self.current_candidate = candidate_info
        self.job_requirements = job_requirements
        self.conversation_history = []

        opening_message = f"Hello! Welcome to the interview for the {job_requirements.get('role', 'position')} role. I'm excited to learn more about your background. Let's start with a simple question: What interests you most about this opportunity?"

        self.conversation_history.append({
            'role': 'ai',
            'message': opening_message,
            'timestamp': datetime.now().isoformat(),
            'confidence': 1.0
        })

        return opening_message

    def conduct_enhanced_voice_turn(self) -> Tuple[str, str, Dict]:
        """Conduct enhanced voice interview turn with detailed feedback"""
        turn_info = {
            'listening_duration': 0,
            'processing_duration': 0,
            'confidence': 0.0,
            'retry_count': 0,
            'status': 'success'
        }

        try:
            # Speak the last AI message
            if self.conversation_history and self.conversation_history[-1]['role'] == 'ai':
                last_message = self.conversation_history[-1]['message']
                self.speak_with_feedback(last_message)
                time.sleep(0.5)  # Brief pause

            # Enhanced listening
            start_time = time.time()
            candidate_speech, confidence = self.advanced_listen_for_speech(timeout=self.listening_timeout)
            turn_info['listening_duration'] = time.time() - start_time
            turn_info['confidence'] = confidence

            # Handle different response types
            if candidate_speech == "TIMEOUT":
                timeout_response = "I didn't hear anything. Are you still there? Please feel free to respond or ask any questions."
                self.conversation_history.append({
                    'role': 'ai',
                    'message': timeout_response,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 1.0
                })
                turn_info['status'] = 'timeout'
                return "TIMEOUT", timeout_response, turn_info

            elif candidate_speech == "UNCLEAR":
                unclear_response = "I'm sorry, I didn't catch that clearly. Could you please speak a bit louder or repeat your response?"
                self.conversation_history.append({
                    'role': 'ai',
                    'message': unclear_response,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 1.0
                })
                turn_info['status'] = 'unclear'
                return "UNCLEAR", unclear_response, turn_info

            elif candidate_speech == "ERROR":
                error_response = "I'm having trouble with the audio. Let's continue with text input for now."
                turn_info['status'] = 'error'
                return "ERROR", error_response, turn_info

            # Add candidate response
            self.conversation_history.append({
                'role': 'user',
                'message': candidate_speech,
                'timestamp': datetime.now().isoformat(),
                'confidence': confidence
            })

            # Generate AI response
            start_time = time.time()
            ai_response = self.generate_ai_response_with_retry(candidate_speech)
            turn_info['processing_duration'] = time.time() - start_time

            # Add AI response
            self.conversation_history.append({
                'role': 'ai',
                'message': ai_response,
                'timestamp': datetime.now().isoformat(),
                'confidence': 1.0
            })

            return candidate_speech, ai_response, turn_info

        except Exception as e:
            logger.error(f"Error in enhanced voice turn: {e}")
            error_response = "I encountered a technical issue. Let's continue with the interview."
            turn_info['status'] = 'error'
            return "ERROR", error_response, turn_info

    def get_listening_status(self) -> Dict[str, Any]:
        """Get current listening status for UI feedback"""
        return {
            'is_listening': self.is_listening,
            'is_processing': self.is_processing,
            'is_speaking': self.is_speaking,
            'last_confidence': self.transcription_confidence
        }
