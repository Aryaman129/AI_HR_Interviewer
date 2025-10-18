"""
Voice-Enabled AI Interview Engine
Complete implementation with speech recognition and text-to-speech
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
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceInterviewEngine:
    """Advanced voice-enabled interview engine with real AI"""

    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self._setup_tts()

        # Ollama configuration
        self.ollama_url = "http://localhost:11434"
        self.model_name = "llama3:latest"

        # Audio settings
        self.sample_rate = 44100
        self.channels = 1
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.is_speaking = False

        # Interview state
        self.conversation_history = []
        self.current_candidate = None
        self.job_requirements = None

        # Calibrate microphone
        self._calibrate_microphone()

    def _setup_tts(self):
        """Configure text-to-speech settings"""
        voices = self.tts_engine.getProperty('voices')

        # Try to find a professional-sounding voice
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

        # Set speech rate and volume
        self.tts_engine.setProperty('rate', 180)  # Slightly slower for clarity
        self.tts_engine.setProperty('volume', 0.9)

    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Microphone calibrated successfully")
        except Exception as e:
            logger.error(f"Microphone calibration failed: {e}")

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

    def speak(self, text):
        """Convert text to speech"""
        if self.is_speaking:
            return

        self.is_speaking = True
        try:
            logger.info(f"AI Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS Error: {e}")
        finally:
            self.is_speaking = False

    def listen_for_speech(self, timeout=10):
        """Listen for speech input with timeout"""
        try:
            with self.microphone as source:
                logger.info("Listening for speech...")
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=30)

                logger.info("Processing speech...")
                # Recognize speech using Google's service
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
                return text

        except sr.WaitTimeoutError:
            return "TIMEOUT"
        except sr.UnknownValueError:
            return "UNCLEAR"
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return "ERROR"
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {e}")
            return "ERROR"

    def generate_ai_response(self, user_message, context=""):
        """Generate AI response using Ollama"""
        try:
            # Build comprehensive context
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
6. Keep responses concise but informative (2-3 sentences max)
7. Show genuine interest in the candidate's background and motivations

Remember: This is a two-way conversation. Be responsive to what the candidate says and asks."""

            # Add conversation history for context
            conversation_context = ""
            if self.conversation_history:
                conversation_context = "\n\nRecent conversation:\n"
                for entry in self.conversation_history[-3:]:  # Last 3 exchanges
                    role = "Interviewer" if entry['role'] == 'ai' else "Candidate"
                    conversation_context += f"{role}: {entry['message']}\n"

            prompt = f"{system_prompt}{conversation_context}\n\nCandidate just said: \"{user_message}\"\n\nYour response as the interviewer:"

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100,
                        "top_p": 0.9,
                        "num_ctx": 2048
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                ai_response = response.json()['response'].strip()
                # Clean up the response
                if ai_response.startswith('"') and ai_response.endswith('"'):
                    ai_response = ai_response[1:-1]
                return ai_response
            else:
                return f"I apologize, I'm having technical difficulties. Could you please repeat that?"

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return "I'm sorry, I didn't catch that. Could you please repeat your response?"

    def start_interview(self, candidate_info, job_requirements):
        """Start voice interview session"""
        self.current_candidate = candidate_info
        self.job_requirements = job_requirements
        self.conversation_history = []

        # Generate opening message
        opening_context = f"""
        Start a professional interview for the {job_requirements.get('role', 'position')} role.
        The candidate's resume shows experience with: {', '.join(candidate_info.get('parsed_info', {}).get('skills', [])[:5])}.
        Begin with a warm greeting and the first interview question.
        """

        opening_message = self.generate_ai_response("Hello, I'm ready for the interview.", opening_context)

        # Add to conversation history
        self.conversation_history.append({
            'role': 'ai',
            'message': opening_message,
            'timestamp': datetime.now().isoformat()
        })

        return opening_message

    def conduct_voice_interview_turn(self):
        """Conduct one turn of voice interview (listen -> process -> respond)"""
        try:
            # Speak the last AI message if there is one
            if self.conversation_history and self.conversation_history[-1]['role'] == 'ai':
                last_message = self.conversation_history[-1]['message']
                self.speak(last_message)

                # Wait a moment for speech to finish
                time.sleep(1)

            # Listen for candidate response
            candidate_speech = self.listen_for_speech(timeout=15)

            if candidate_speech == "TIMEOUT":
                timeout_response = "I didn't hear anything. Are you still there? Please feel free to respond or ask any questions."
                self.conversation_history.append({
                    'role': 'ai',
                    'message': timeout_response,
                    'timestamp': datetime.now().isoformat()
                })
                return "TIMEOUT", timeout_response

            elif candidate_speech == "UNCLEAR":
                unclear_response = "I'm sorry, I didn't catch that clearly. Could you please repeat your response?"
                self.conversation_history.append({
                    'role': 'ai',
                    'message': unclear_response,
                    'timestamp': datetime.now().isoformat()
                })
                return "UNCLEAR", unclear_response

            elif candidate_speech == "ERROR":
                error_response = "I'm having trouble with the audio. Let's continue with text input for now."
                return "ERROR", error_response

            # Add candidate response to history
            self.conversation_history.append({
                'role': 'user',
                'message': candidate_speech,
                'timestamp': datetime.now().isoformat()
            })

            # Generate AI response
            ai_response = self.generate_ai_response(candidate_speech)

            # Add AI response to history
            self.conversation_history.append({
                'role': 'ai',
                'message': ai_response,
                'timestamp': datetime.now().isoformat()
            })

            return candidate_speech, ai_response

        except Exception as e:
            logger.error(f"Error in voice interview turn: {e}")
            error_response = "I encountered a technical issue. Let's continue with the interview."
            return "ERROR", error_response

    def save_interview_log(self, filename=None):
        """Save interview conversation to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            candidate_name = self.current_candidate.get('filename', 'unknown').replace('.txt', '')
            filename = f"interview_{candidate_name}_{timestamp}.json"

        log_data = {
            'candidate': self.current_candidate,
            'job_requirements': self.job_requirements,
            'conversation': self.conversation_history,
            'interview_date': datetime.now().isoformat(),
            'total_exchanges': len([entry for entry in self.conversation_history if entry['role'] == 'user'])
        }

        # Save to chat logs directory
        log_path = Path("frontend/chat_logs") / filename
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Interview log saved: {log_path}")
        return str(log_path)

    def get_interview_summary(self):
        """Generate interview summary and scoring"""
        if not self.conversation_history:
            return {"error": "No interview data available"}

        user_responses = [entry for entry in self.conversation_history if entry['role'] == 'user']

        if not user_responses:
            return {"error": "No candidate responses recorded"}

        # Calculate basic metrics
        total_responses = len(user_responses)
        avg_response_length = sum(len(response['message'].split()) for response in user_responses) / total_responses
        total_duration = len(self.conversation_history) * 2  # Rough estimate in minutes

        # Simple scoring algorithm
        communication_score = min(100, (avg_response_length / 20) * 100)  # Based on response detail
        engagement_score = min(100, (total_responses / 5) * 100)  # Based on number of responses
        overall_score = (communication_score + engagement_score) / 2

        return {
            'candidate': self.current_candidate.get('filename', 'Unknown'),
            'total_responses': total_responses,
            'avg_response_length': round(avg_response_length, 1),
            'estimated_duration': f"{total_duration} minutes",
            'scores': {
                'communication': round(communication_score, 1),
                'engagement': round(engagement_score, 1),
                'overall': round(overall_score, 1)
            },
            'recommendation': 'Recommended' if overall_score >= 70 else 'Consider' if overall_score >= 50 else 'Not Recommended'
        }
