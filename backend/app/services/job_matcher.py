"""
Advanced Job-Candidate Matching Service
Using JobBERT-v3 (768-dim) embeddings and cosine similarity
"""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
from sqlalchemy.orm import Session
from ..models.job import Job
from ..models.candidate import Candidate
from ..db.database import get_db
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

class JobCandidateMatchingService:
    """
    Advanced job-candidate matching using:
    - JobBERT-v3 (768-dim) for semantic embeddings
    - dslim/bert-base-NER for entity extraction (76.3M downloads)
    - Custom scoring algorithm combining multiple factors
    """
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Use embedding service for 768-dim JobBERT-v3 embeddings
        self.embedding_service = get_embedding_service()
        
        # Load BERT-based NER model (discovered through HF research)
        self.ner_tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
        self.ner_model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
        self.ner_pipeline = pipeline(
            "ner",
            model=self.ner_model,
            tokenizer=self.ner_tokenizer,
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1
        )
        
        logger.info("JobCandidateMatchingService initialized with JobBERT-v3 (768-dim)")
    
    def extract_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """
        Extract structured requirements from job description
        using advanced NER and custom parsing
        """
        # Extract entities using BERT-based NER
        entities = self.ner_pipeline(job_description)
        
        requirements = {
            "skills": [],
            "organizations": [],
            "locations": [],
            "experience_years": None,
            "education_level": None,
            "key_phrases": []
        }
        
        # Process NER entities
        for entity in entities:
            if entity['entity_group'] == 'ORG':
                requirements["organizations"].append(entity['word'])
            elif entity['entity_group'] == 'LOC':
                requirements["locations"].append(entity['word'])
        
        # Extract skills using keyword matching (enhanced approach)
        skill_keywords = self._extract_skills_from_text(job_description)
        requirements["skills"] = skill_keywords
        
        # Extract experience requirements
        requirements["experience_years"] = self._extract_experience_years(job_description)
        
        # Extract education requirements
        requirements["education_level"] = self._extract_education_level(job_description)
        
        return requirements
    
    def calculate_match_score(
        self, 
        candidate_id: int, 
        job_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score between candidate and job
        """
        # Get candidate and job data
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not candidate or not job:
            return {"error": "Candidate or job not found"}
        
        # Extract job requirements
        job_requirements = self.extract_job_requirements(job.description)
        
        # Calculate different scoring components
        scores = {
            "semantic_similarity": self._calculate_semantic_similarity(
                candidate, job
            ),
            "skills_match": self._calculate_skills_match(
                candidate.skills, job_requirements["skills"]
            ),
            "experience_match": self._calculate_experience_match(
                candidate.experience_years, job_requirements["experience_years"]
            ),
            "education_match": self._calculate_education_match(
                candidate.education, job_requirements["education_level"]
            ),
            "location_match": self._calculate_location_match(
                candidate.location, job_requirements["locations"]
            )
        }
        
        # Calculate weighted overall score
        weights = {
            "semantic_similarity": 0.35,
            "skills_match": 0.30,
            "experience_match": 0.20,
            "education_match": 0.10,
            "location_match": 0.05
        }
        
        overall_score = sum(
            scores[component] * weights[component] 
            for component in scores
        )
        
        return {
            "overall_score": round(overall_score, 3),
            "component_scores": scores,
            "job_requirements": job_requirements,
            "match_explanation": self._generate_match_explanation(scores, job_requirements)
        }
    
    def find_best_candidates(
        self, 
        job_id: int, 
        db: Session, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find best matching candidates for a job
        """
        candidates = db.query(Candidate).all()
        candidate_scores = []
        
        for candidate in candidates:
            score_data = self.calculate_match_score(candidate.id, job_id, db)
            if "error" not in score_data:
                candidate_scores.append({
                    "candidate_id": candidate.id,
                    "candidate_name": f"{candidate.first_name} {candidate.last_name}",
                    "score": score_data["overall_score"],
                    "component_scores": score_data["component_scores"],
                    "explanation": score_data["match_explanation"]
                })
        
        # Sort by score and return top candidates
        candidate_scores.sort(key=lambda x: x["score"], reverse=True)
        return candidate_scores[:limit]
    
    def _calculate_semantic_similarity(self, candidate, job) -> float:
        """
        Calculate semantic similarity using JobBERT-v3 (768-dim) embeddings
        Uses pre-computed embeddings from database if available
        """
        try:
            # Try to use pre-computed embeddings from database (768-dim)
            if candidate.resume_embedding is not None and len(candidate.resume_embedding) == 768:
                candidate_embedding = np.array(candidate.resume_embedding)
            else:
                # Generate new embedding if not available
                candidate_text = f"{candidate.summary} {' '.join(candidate.skills.get('technical', [])) if candidate.skills else ''}"
                candidate_emb_list = self.embedding_service.generate_text_embedding(candidate_text)
                candidate_embedding = np.array(candidate_emb_list)
            
            if job.job_description_embedding is not None and len(job.job_description_embedding) == 768:
                job_embedding = np.array(job.job_description_embedding)
            else:
                # Generate new embedding if not available
                job_emb_list = self.embedding_service.generate_text_embedding(job.description)
                job_embedding = np.array(job_emb_list)
            
            # Calculate cosine similarity using embedding service
            similarity = self.embedding_service.cosine_similarity(
                candidate_embedding,
                job_embedding
            )
            
            logger.debug(f"Semantic similarity: {similarity:.3f} (using 768-dim JobBERT-v3)")
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.5  # Return neutral score on error
    
    def _calculate_skills_match(self, candidate_skills: Dict[str, List[str]], required_skills: List[str]) -> float:
        """
        Calculate skills match score
        Candidate skills is a dict with 'technical' and 'soft' keys
        """
        if not candidate_skills or not required_skills:
            return 0.0
        
        # Extract all skills from candidate (technical + soft)
        all_candidate_skills = []
        if isinstance(candidate_skills, dict):
            all_candidate_skills.extend(candidate_skills.get('technical', []))
            all_candidate_skills.extend(candidate_skills.get('soft', []))
        elif isinstance(candidate_skills, list):
            all_candidate_skills = candidate_skills
        
        if not all_candidate_skills:
            return 0.0
        
        candidate_skills_lower = [skill.lower() for skill in all_candidate_skills]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        matched_skills = set(candidate_skills_lower) & set(required_skills_lower)
        match_ratio = len(matched_skills) / len(required_skills_lower)
        
        logger.debug(f"Skills match: {len(matched_skills)}/{len(required_skills_lower)} = {match_ratio:.2f}")
        return min(match_ratio, 1.0)
    
    def _calculate_experience_match(self, candidate_exp: int, required_exp: int) -> float:
        """
        Calculate experience match score
        """
        if required_exp is None or candidate_exp is None:
            return 0.5  # Neutral score if information missing
        
        if candidate_exp >= required_exp:
            return 1.0
        else:
            # Partial credit for partial experience
            return max(0.0, candidate_exp / required_exp)
    
    def _calculate_education_match(self, candidate_education: str, required_education: str) -> float:
        """
        Calculate education match score
        """
        if not candidate_education or not required_education:
            return 0.5
        
        education_hierarchy = {
            "high school": 1,
            "diploma": 2,
            "bachelor": 3,
            "master": 4,
            "phd": 5,
            "doctorate": 5
        }
        
        candidate_level = self._get_education_level(candidate_education, education_hierarchy)
        required_level = self._get_education_level(required_education, education_hierarchy)
        
        if candidate_level >= required_level:
            return 1.0
        else:
            return max(0.0, candidate_level / required_level)
    
    def _calculate_location_match(self, candidate_location: str, required_locations: List[str]) -> float:
        """
        Calculate location match score
        """
        if not candidate_location or not required_locations:
            return 0.5
        
        candidate_location_lower = candidate_location.lower()
        for location in required_locations:
            if location.lower() in candidate_location_lower:
                return 1.0
        
        return 0.0
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from text using enhanced keyword matching
        """
        # Common technology skills (expand based on your domain)
        skill_keywords = [
            "python", "java", "javascript", "react", "angular", "vue",
            "nodejs", "django", "flask", "fastapi", "spring", "sql",
            "postgresql", "mysql", "mongodb", "docker", "kubernetes",
            "aws", "azure", "gcp", "machine learning", "ai", "data science",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy"
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_experience_years(self, text: str) -> int:
        """
        Extract required experience years from job description
        """
        import re
        
        # Look for patterns like "2+ years", "3-5 years experience"
        patterns = [
            r"(\d+)\+?\s*years?\s*(?:of\s*)?experience",
            r"(\d+)\s*to\s*\d+\s*years?",
            r"minimum\s*(\d+)\s*years?",
            r"at\s*least\s*(\d+)\s*years?"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_education_level(self, text: str) -> str:
        """
        Extract required education level from job description
        """
        text_lower = text.lower()
        
        if "phd" in text_lower or "doctorate" in text_lower:
            return "phd"
        elif "master" in text_lower or "mba" in text_lower:
            return "master"
        elif "bachelor" in text_lower or "degree" in text_lower:
            return "bachelor"
        elif "diploma" in text_lower:
            return "diploma"
        elif "high school" in text_lower:
            return "high school"
        
        return None
    
    def _get_education_level(self, education_text: str, hierarchy: Dict[str, int]) -> int:
        """
        Get numeric education level from text
        """
        education_lower = education_text.lower()
        
        for level, value in hierarchy.items():
            if level in education_lower:
                return value
        
        return 1  # Default to high school level
    
    def _generate_match_explanation(self, scores: Dict[str, float], job_requirements: Dict[str, Any]) -> str:
        """
        Generate human-readable match explanation
        """
        explanations = []
        
        if scores["semantic_similarity"] > 0.7:
            explanations.append("Strong semantic match with job description")
        elif scores["semantic_similarity"] > 0.5:
            explanations.append("Good semantic alignment with job requirements")
        else:
            explanations.append("Limited semantic match with job description")
        
        if scores["skills_match"] > 0.8:
            explanations.append("Excellent skills match")
        elif scores["skills_match"] > 0.5:
            explanations.append("Good skills overlap")
        else:
            explanations.append("Limited skills match")
        
        if scores["experience_match"] > 0.8:
            explanations.append("Meets experience requirements")
        elif scores["experience_match"] > 0.5:
            explanations.append("Partially meets experience requirements")
        else:
            explanations.append("Below experience requirements")
        
        return " | ".join(explanations)

# Singleton instance
job_matcher_service = JobCandidateMatchingService()