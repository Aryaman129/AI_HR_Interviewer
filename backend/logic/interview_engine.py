"""
AI Interview Engine for conducting voice and text interviews
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import requests
import whisper
from TTS.api import TTS
import sounddevice as sd
import soundfile as sf
import numpy as np
from threading import Thread
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterviewEngine:
    def __init__(self, config_path: str = "config/app_config.json"):
        """Initialize the interview engine"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Load interview questions
        with open("config/interview_questions.json", 'r') as f:
            self.questions_config = json.load(f)
        
        # Initialize models
        self._init_models()
        
        # Interview state
        self.current_interview = None
        self.interview_log = []
        self.audio_queue = queue.Queue()
        
        # Paths
        self.audio_logs_path = Path(self.config['paths']['audio_logs'])
        self.chat_logs_path = Path(self.config['paths']['chat_logs'])
        
        # Create directories
        self.audio_logs_path.mkdir(parents=True, exist_ok=True)
        self.chat_logs_path.mkdir(parents=True, exist_ok=True)
    
    def _init_models(self):
        """Initialize AI models"""
        try:
            # Initialize Whisper for speech-to-text
            whisper_model = self.config['models']['whisper']['model_size']
            self.whisper_model = whisper.load_model(whisper_model)
            logger.info(f"Whisper model '{whisper_model}' loaded successfully")
            
            # Initialize TTS
            tts_model = self.config['models']['tts']['model_name']
            self.tts = TTS(model_name=tts_model, progress_bar=False)
            logger.info(f"TTS model '{tts_model}' loaded successfully")
            
            # Ollama configuration
            self.ollama_config = self.config['models']['llm']
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise
    
    def start_interview(self, candidate_info: Dict[str, Any], job_requirements: Dict[str, Any]) -> str:
        """Start a new interview session"""
        interview_id = str(uuid.uuid4())
        
        self.current_interview = {
            'id': interview_id,
            'candidate': candidate_info,
            'job_requirements': job_requirements,
            'start_time': datetime.now().isoformat(),
            'status': 'active',
            'current_question_index': 0,
            'questions_asked': [],
            'responses': [],
            'scores': {},
            'notes': []
        }
        
        self.interview_log = []
        
        # Generate interview plan
        self._generate_interview_plan()
        
        # Start with greeting
        greeting = self._generate_greeting()
        self._add_to_log("AI", greeting)
        
        logger.info(f"Interview started for candidate: {candidate_info.get('filename', 'Unknown')}")
        return interview_id
    
    def _generate_interview_plan(self):
        """Generate a customized interview plan based on candidate and job requirements"""
        plan = []
        
        # Add core questions
        for question in self.questions_config['core_questions']:
            plan.append({
                'type': 'core',
                'question': question['question'],
                'category': question['category'],
                'required': question['required']
            })
        
        # Add role-specific questions
        job_role = self.current_interview['job_requirements'].get('role', '').lower()
        role_questions = []
        
        # Map job roles to question categories
        if any(keyword in job_role for keyword in ['software', 'developer', 'engineer', 'programmer']):
            role_questions = self.questions_config['role_specific_templates'].get('software_engineer', [])
        elif any(keyword in job_role for keyword in ['security', 'cybersecurity', 'infosec']):
            role_questions = self.questions_config['role_specific_templates'].get('cybersecurity', [])
        elif any(keyword in job_role for keyword in ['data', 'scientist', 'analyst']):
            role_questions = self.questions_config['role_specific_templates'].get('data_scientist', [])
        elif any(keyword in job_role for keyword in ['product', 'manager']):
            role_questions = self.questions_config['role_specific_templates'].get('product_manager', [])
        
        for question in role_questions[:3]:  # Limit to 3 role-specific questions
            plan.append({
                'type': 'role_specific',
                'question': question,
                'category': 'technical'
            })
        
        # Add resume verification questions
        candidate_skills = self.current_interview['candidate']['parsed_info'].get('skills', [])
        for skill in candidate_skills[:2]:  # Verify top 2 skills
            verification_question = f"Can you elaborate on your experience with {skill}?"
            plan.append({
                'type': 'verification',
                'question': verification_question,
                'category': 'experience_verification',
                'skill': skill
            })
        
        self.current_interview['interview_plan'] = plan
    
    def _generate_greeting(self) -> str:
        """Generate a personalized greeting"""
        candidate_name = self.current_interview['candidate'].get('filename', 'candidate').replace('.pdf', '').replace('.docx', '')
        job_role = self.current_interview['job_requirements'].get('role', 'this position')
        
        greeting = f"""Hello! Welcome to the AI interview for the {job_role} position. 
        I'm your AI interviewer today. This interview will take approximately 20-30 minutes, 
        and I'll be asking you questions about your background, experience, and suitability for the role.
        
        Please speak clearly, and feel free to ask for clarification if needed. 
        Let's begin with some basic questions. Are you ready to start?"""
        
        return greeting
    
    def get_next_question(self) -> Optional[str]:
        """Get the next question in the interview"""
        if not self.current_interview or self.current_interview['status'] != 'active':
            return None
        
        plan = self.current_interview['interview_plan']
        current_index = self.current_interview['current_question_index']
        
        if current_index >= len(plan):
            return self._generate_closing()
        
        question_data = plan[current_index]
        question = question_data['question']
        
        # Add to questions asked
        self.current_interview['questions_asked'].append(question_data)
        self.current_interview['current_question_index'] += 1
        
        return question
    
    def process_response(self, response_text: str) -> Dict[str, Any]:
        """Process candidate response and generate follow-up or next question"""
        if not self.current_interview:
            return {'error': 'No active interview'}
        
        # Add response to log
        self._add_to_log("Candidate", response_text)
        
        # Store response
        self.current_interview['responses'].append({
            'question_index': self.current_interview['current_question_index'] - 1,
            'response': response_text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Analyze response and determine next action
        analysis = self._analyze_response(response_text)
        
        # Generate AI response
        ai_response = self._generate_ai_response(response_text, analysis)
        
        # Check if follow-up is needed
        if analysis.get('needs_followup', False):
            followup = self._generate_followup_question(response_text, analysis)
            if followup:
                self._add_to_log("AI", followup)
                return {
                    'type': 'followup',
                    'message': followup,
                    'analysis': analysis
                }
        
        # Get next question
        next_question = self.get_next_question()
        if next_question:
            self._add_to_log("AI", next_question)
            return {
                'type': 'next_question',
                'message': next_question,
                'analysis': analysis
            }
        else:
            # Interview complete
            self._complete_interview()
            return {
                'type': 'complete',
                'message': "Thank you for your time. The interview is now complete.",
                'analysis': analysis
            }
    
    def _analyze_response(self, response: str) -> Dict[str, Any]:
        """Analyze candidate response for quality and completeness"""
        analysis = {
            'word_count': len(response.split()),
            'confidence_score': 0.7,  # Default confidence
            'needs_followup': False,
            'sentiment': 'neutral',
            'key_points': []
        }
        
        # Simple analysis rules
        if analysis['word_count'] < 10:
            analysis['needs_followup'] = True
            analysis['confidence_score'] = 0.3
        elif analysis['word_count'] < 30:
            analysis['needs_followup'] = True
            analysis['confidence_score'] = 0.5
        
        # Check for vague responses
        vague_indicators = ['maybe', 'i think', 'probably', 'not sure', 'i guess']
        if any(indicator in response.lower() for indicator in vague_indicators):
            analysis['needs_followup'] = True
            analysis['confidence_score'] *= 0.8
        
        return analysis
    
    def _generate_ai_response(self, candidate_response: str, analysis: Dict[str, Any]) -> str:
        """Generate AI response using Ollama"""
        try:
            # Prepare context
            context = self._build_context_for_llm(candidate_response)
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_config['base_url']}/api/generate",
                json={
                    "model": self.ollama_config['model_name'],
                    "prompt": context,
                    "stream": False,
                    "options": {
                        "temperature": self.ollama_config['temperature'],
                        "num_predict": self.ollama_config['max_tokens']
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()['response'].strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "I understand. Let me ask you the next question."
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Thank you for your response. Let's continue."
    
    def _build_context_for_llm(self, candidate_response: str) -> str:
        """Build context for LLM prompt"""
        job_role = self.current_interview['job_requirements'].get('role', 'this position')
        
        context = f"""You are an AI interviewer conducting a professional job interview for a {job_role} position.
        
        The candidate just responded: "{candidate_response}"
        
        Generate a brief, professional acknowledgment (1-2 sentences) that:
        1. Acknowledges their response appropriately
        2. Maintains a professional, friendly tone
        3. Transitions naturally to the next part of the interview
        
        Keep it concise and natural. Do not ask follow-up questions in this response.
        
        Response:"""
        
        return context
    
    def _generate_followup_question(self, response: str, analysis: Dict[str, Any]) -> Optional[str]:
        """Generate a follow-up question based on response analysis"""
        followup_patterns = self.questions_config['followup_patterns']
        
        if analysis['word_count'] < 20:
            return np.random.choice(followup_patterns['insufficient_detail'])
        
        # Check current question type for specific follow-ups
        current_question = self.current_interview['questions_asked'][-1]
        if current_question['category'] in ['technical', 'experience_verification']:
            return np.random.choice(followup_patterns['technical_depth'])
        
        return np.random.choice(followup_patterns['behavioral'])
    
    def _generate_closing(self) -> str:
        """Generate interview closing message"""
        return """Thank you for taking the time to speak with us today. 
        We've covered all the questions I had prepared. Do you have any questions 
        about the role or our company before we conclude?"""
    
    def _add_to_log(self, speaker: str, message: str):
        """Add entry to interview log"""
        self.interview_log.append({
            'timestamp': datetime.now().isoformat(),
            'speaker': speaker,
            'message': message
        })
    
    def _complete_interview(self):
        """Complete the interview and save logs"""
        if not self.current_interview:
            return
        
        self.current_interview['status'] = 'completed'
        self.current_interview['end_time'] = datetime.now().isoformat()
        
        # Calculate final scores
        self.current_interview['final_score'] = self._calculate_final_score()
        
        # Save interview log
        log_file = self.chat_logs_path / f"{self.current_interview['id']}.json"
        with open(log_file, 'w') as f:
            json.dump({
                'interview_data': self.current_interview,
                'conversation_log': self.interview_log
            }, f, indent=2)
        
        logger.info(f"Interview completed and saved: {log_file}")
    
    def _calculate_final_score(self) -> Dict[str, Any]:
        """Calculate final interview score"""
        # Simple scoring based on response quality
        total_responses = len(self.current_interview['responses'])
        if total_responses == 0:
            return {'overall': 0, 'breakdown': {}}
        
        # Calculate average response quality
        avg_word_count = np.mean([len(r['response'].split()) for r in self.current_interview['responses']])
        
        # Simple scoring logic
        communication_score = min(100, (avg_word_count / 50) * 100)
        technical_score = 75  # Placeholder - would need more sophisticated analysis
        experience_score = 70  # Based on resume match score
        
        weights = self.config['scoring']
        overall_score = (
            technical_score * weights['technical_weight'] +
            communication_score * weights['communication_weight'] +
            experience_score * weights['experience_weight']
        )
        
        return {
            'overall': round(overall_score, 2),
            'breakdown': {
                'technical': round(technical_score, 2),
                'communication': round(communication_score, 2),
                'experience': round(experience_score, 2)
            },
            'recommendation': 'Recommended' if overall_score >= 65 else 'Not Recommended'
        }
    
    def get_interview_status(self) -> Dict[str, Any]:
        """Get current interview status"""
        if not self.current_interview:
            return {'status': 'no_active_interview'}
        
        return {
            'status': self.current_interview['status'],
            'progress': f"{self.current_interview['current_question_index']}/{len(self.current_interview['interview_plan'])}",
            'duration': self._calculate_duration(),
            'questions_remaining': len(self.current_interview['interview_plan']) - self.current_interview['current_question_index']
        }
    
    def _calculate_duration(self) -> str:
        """Calculate interview duration"""
        if not self.current_interview:
            return "0:00"
        
        start_time = datetime.fromisoformat(self.current_interview['start_time'])
        duration = datetime.now() - start_time
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        return f"{minutes}:{seconds:02d}"
