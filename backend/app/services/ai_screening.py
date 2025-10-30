"""
AI Screening Service
Generates interview questions and evaluates responses using Ollama
Based on research from AI interview systems on HuggingFace
"""

import json
import logging
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.screening import Screening, ScreeningStatus

logger = logging.getLogger(__name__)

class QuestionType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    DOMAIN_SPECIFIC = "domain_specific"

class DifficultyLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"

class AIScreeningService:
    """
    AI-powered screening service using Ollama
    Generates contextual questions and evaluates responses
    """
    
    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.session_timeout = 300  # 5 minutes
        
    async def generate_screening_questions(
        self,
        job_id: int,
        candidate_id: int,
        db: Session,
        num_questions: int = 5,
        question_types: Optional[List[QuestionType]] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized screening questions based on job and candidate profile
        """
        # Get job and candidate data
        job = db.query(Job).filter(Job.id == job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not job or not candidate:
            raise ValueError("Job or candidate not found")
        
        # Default question types
        if not question_types:
            question_types = [
                QuestionType.TECHNICAL,
                QuestionType.BEHAVIORAL,
                QuestionType.SITUATIONAL
            ]
        
        # Create context for AI
        context = self._build_question_context(job, candidate)
        
        # Generate questions using Ollama
        questions = await self._generate_questions_with_ollama(
            context, num_questions, question_types
        )
        
        # Create screening record
        screening = Screening(
            job_id=job_id,
            candidate_id=candidate_id,
            questions=questions,
            status=ScreeningStatus.IN_PROGRESS,
            created_at=datetime.utcnow()
        )
        
        db.add(screening)
        db.commit()
        db.refresh(screening)
        
        logger.info(f"Generated {len(questions)} questions for screening {screening.id}")
        
        return {
            "screening_id": screening.id,
            "questions": questions,
            "job_title": job.title,
            "candidate_name": candidate.full_name,
            "estimated_duration": len(questions) * 3  # 3 minutes per question
        }
    
    async def evaluate_response(
        self,
        screening_id: int,
        question_id: str,
        response: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's response to a screening question
        """
        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise ValueError("Screening not found")
        
        # Find the specific question
        question = None
        for q in screening.questions:
            if q.get("id") == question_id:
                question = q
                break
        
        if not question:
            raise ValueError("Question not found")
        
        # Evaluate using Ollama
        evaluation = await self._evaluate_response_with_ollama(question, response, screening)
        
        # Update screening record
        if not screening.responses:
            screening.responses = []
        
        screening.responses.append({
            "question_id": question_id,
            "response": response,
            "evaluation": evaluation,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check if all questions are answered
        answered_questions = len(screening.responses)
        total_questions = len(screening.questions)
        
        if answered_questions >= total_questions:
            screening.status = ScreeningStatus.COMPLETED
            screening.overall_score = self._calculate_overall_score(screening.responses)
            screening.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(screening)
        
        return {
            "evaluation": evaluation,
            "progress": f"{answered_questions}/{total_questions}",
            "completed": screening.status == ScreeningStatus.COMPLETED,
            "overall_score": screening.overall_score
        }
    
    async def get_screening_summary(self, screening_id: int, db: Session) -> Dict[str, Any]:
        """
        Get comprehensive screening summary with AI insights
        """
        screening = db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            raise ValueError("Screening not found")
        
        job = db.query(Job).filter(Job.id == screening.job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == screening.candidate_id).first()
        
        # Generate AI summary
        summary = await self._generate_screening_summary(screening, job, candidate)
        
        return {
            "screening_id": screening_id,
            "job_title": job.title,
            "candidate_name": candidate.full_name,
            "status": screening.status,
            "overall_score": screening.overall_score,
            "questions_answered": len(screening.responses or []),
            "total_questions": len(screening.questions),
            "duration_minutes": self._calculate_duration(screening),
            "ai_summary": summary,
            "responses": screening.responses,
            "recommendations": self._generate_recommendations(screening)
        }
    
    def _build_question_context(self, job: Job, candidate: Candidate) -> Dict[str, Any]:
        """
        Build context for question generation
        """
        return {
            "job": {
                "title": job.title,
                "description": job.description,
                "requirements": job.requirements,
                "skills_required": job.skills_required,
                "experience_level": job.experience_level,
                "department": job.department
            },
            "candidate": {
                "name": candidate.full_name,
                "skills": candidate.skills,
                "education": candidate.education,
                "experience": candidate.work_experience,
                "total_experience_years": candidate.total_experience_years
            }
        }
    
    async def _generate_questions_with_ollama(
        self,
        context: Dict[str, Any],
        num_questions: int,
        question_types: List[QuestionType]
    ) -> List[Dict[str, Any]]:
        """
        Generate questions using Ollama LLM
        """
        prompt = f"""
        You are an AI HR specialist conducting a screening interview. Generate {num_questions} diverse screening questions based on the following context:

        JOB DETAILS:
        Title: {context['job']['title']}
        Description: {context['job']['description']}
        Required Skills: {', '.join(context['job']['skills_required'] or [])}
        Experience Level: {context['job']['experience_level']}

        CANDIDATE PROFILE:
        Name: {context['candidate']['name']}
        Skills: {context['candidate']['skills']}
        Experience: {context['candidate']['total_experience_years']} years

        QUESTION TYPES TO INCLUDE: {', '.join(question_types)}

        Generate questions that are:
        1. Relevant to the job requirements
        2. Appropriate for the candidate's experience level
        3. Mix of technical, behavioral, and situational questions
        4. Clear and concise
        5. Include expected answer criteria

        Return ONLY valid JSON in this exact format:
        {{
            "questions": [
                {{
                    "id": "q1",
                    "type": "technical",
                    "question": "Question text here?",
                    "expected_skills": ["skill1", "skill2"],
                    "evaluation_criteria": "What to look for in the answer",
                    "difficulty": "mid",
                    "max_score": 10
                }}
            ]
        }}
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 2000
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # Parse JSON from response
                        try:
                            # Extract JSON from response (sometimes Ollama adds extra text)
                            start = response_text.find('{')
                            end = response_text.rfind('}') + 1
                            json_str = response_text[start:end]
                            
                            questions_data = json.loads(json_str)
                            questions = questions_data.get("questions", [])
                            
                            # Add IDs if missing
                            for i, q in enumerate(questions):
                                if "id" not in q:
                                    q["id"] = f"q{i+1}"
                            
                            return questions[:num_questions]
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON from Ollama: {e}")
                            return self._generate_fallback_questions(context, num_questions)
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return self._generate_fallback_questions(context, num_questions)
                        
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return self._generate_fallback_questions(context, num_questions)
    
    async def _evaluate_response_with_ollama(
        self,
        question: Dict[str, Any],
        response: str,
        screening: Screening
    ) -> Dict[str, Any]:
        """
        Evaluate response using Ollama
        """
        prompt = f"""
        You are an expert HR interviewer evaluating a candidate's response. Provide a detailed evaluation.

        QUESTION: {question['question']}
        QUESTION TYPE: {question.get('type', 'general')}
        EXPECTED SKILLS: {', '.join(question.get('expected_skills', []))}
        EVALUATION CRITERIA: {question.get('evaluation_criteria', 'General assessment')}
        MAX SCORE: {question.get('max_score', 10)}

        CANDIDATE'S RESPONSE: {response}

        Evaluate this response and return ONLY valid JSON:
        {{
            "score": 7,
            "feedback": "Detailed feedback on the response",
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1"],
            "suggestions": "Specific suggestions for improvement",
            "technical_accuracy": 8,
            "communication_clarity": 9,
            "relevance": 7,
            "overall_assessment": "good"
        }}
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Lower temperature for more consistent scoring
                            "num_predict": 1000
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as ollama_response:
                    if ollama_response.status == 200:
                        result = await ollama_response.json()
                        response_text = result.get("response", "")
                        
                        try:
                            # Extract and parse JSON
                            start = response_text.find('{')
                            end = response_text.rfind('}') + 1
                            json_str = response_text[start:end]
                            
                            evaluation = json.loads(json_str)
                            
                            # Ensure score is within bounds
                            max_score = question.get('max_score', 10)
                            evaluation['score'] = min(max_score, max(0, evaluation.get('score', 0)))
                            
                            return evaluation
                            
                        except json.JSONDecodeError:
                            logger.error("Failed to parse evaluation JSON from Ollama")
                            return self._generate_fallback_evaluation(response, question)
                    else:
                        logger.error(f"Ollama evaluation error: {ollama_response.status}")
                        return self._generate_fallback_evaluation(response, question)
                        
        except Exception as e:
            logger.error(f"Error evaluating with Ollama: {e}")
            return self._generate_fallback_evaluation(response, question)
    
    def _generate_fallback_questions(self, context: Dict[str, Any], num_questions: int) -> List[Dict[str, Any]]:
        """
        Generate fallback questions when Ollama is unavailable
        """
        return [
            {
                "id": f"q{i+1}",
                "type": "general",
                "question": f"Tell me about your experience with {skill}." if i < len(context['candidate']['skills']) else "Describe a challenging project you worked on.",
                "expected_skills": [context['candidate']['skills'][i]] if i < len(context['candidate']['skills']) else ["problem-solving"],
                "evaluation_criteria": "Clear explanation with specific examples",
                "difficulty": "mid",
                "max_score": 10
            }
            for i in range(min(num_questions, 5))
        ]
    
    def _generate_fallback_evaluation(self, response: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback evaluation when Ollama is unavailable
        """
        response_length = len(response.split())
        base_score = min(10, max(1, response_length // 10))  # Basic scoring based on length
        
        return {
            "score": base_score,
            "feedback": "Response evaluated using fallback method. Manual review recommended.",
            "strengths": ["Provided a response"],
            "weaknesses": ["Unable to perform detailed AI evaluation"],
            "suggestions": "Please review manually for detailed assessment",
            "technical_accuracy": base_score,
            "communication_clarity": base_score,
            "relevance": base_score,
            "overall_assessment": "requires_manual_review"
        }
    
    def _calculate_overall_score(self, responses: List[Dict[str, Any]]) -> float:
        """
        Calculate overall screening score
        """
        if not responses:
            return 0.0
        
        total_score = sum(r.get('evaluation', {}).get('score', 0) for r in responses)
        max_possible = len(responses) * 10  # Assuming max score of 10 per question
        
        return round((total_score / max_possible) * 100, 2) if max_possible > 0 else 0.0
    
    def _calculate_duration(self, screening: Screening) -> int:
        """
        Calculate screening duration in minutes
        """
        if not screening.completed_at or not screening.created_at:
            return 0
        
        duration = screening.completed_at - screening.created_at
        return int(duration.total_seconds() / 60)
    
    def _generate_recommendations(self, screening: Screening) -> List[str]:
        """
        Generate hiring recommendations based on screening results
        """
        recommendations = []
        score = screening.overall_score or 0
        
        if score >= 80:
            recommendations.append("Strong candidate - Recommend for next round")
            recommendations.append("Demonstrated excellent technical and communication skills")
        elif score >= 65:
            recommendations.append("Good candidate - Consider for interview")
            recommendations.append("Shows potential with some areas for development")
        elif score >= 50:
            recommendations.append("Average candidate - Requires careful consideration")
            recommendations.append("May need additional training or mentorship")
        else:
            recommendations.append("Below threshold - Not recommended for current role")
            recommendations.append("Consider for junior positions or future opportunities")
        
        return recommendations
    
    async def _generate_screening_summary(
        self,
        screening: Screening,
        job: Job,
        candidate: Candidate
    ) -> str:
        """
        Generate AI-powered screening summary
        """
        prompt = f"""
        Generate a concise screening summary for this candidate:

        Job: {job.title}
        Candidate: {candidate.full_name}
        Overall Score: {screening.overall_score}%
        Questions Answered: {len(screening.responses or [])}

        Key Responses:
        {self._format_responses_for_summary(screening.responses or [])}

        Provide a 2-3 sentence professional summary highlighting:
        1. Overall performance
        2. Key strengths
        3. Areas of concern (if any)
        4. Fit for the role
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.5,
                            "num_predict": 300
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "").strip()
                    else:
                        return "AI summary unavailable. Manual review recommended."
                        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "AI summary unavailable due to technical issue. Manual review recommended."
    
    def _format_responses_for_summary(self, responses: List[Dict[str, Any]]) -> str:
        """
        Format responses for summary generation
        """
        formatted = []
        for i, response in enumerate(responses[:3]):  # Include top 3 responses
            evaluation = response.get('evaluation', {})
            score = evaluation.get('score', 0)
            feedback = evaluation.get('feedback', 'No feedback')
            formatted.append(f"Q{i+1} (Score: {score}/10): {feedback[:100]}...")
        
        return "\n".join(formatted)

# Singleton instance
ai_screening_service = AIScreeningService()