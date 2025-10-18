"""
Resume filtering and ranking system for AI HR Interviewer
"""

import os
import json
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
import PyPDF2
import pdfplumber
from docx import Document
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeFilter:
    def __init__(self, config_path: str = "config/app_config.json"):
        """Initialize the resume filter with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize embedding model
        model_name = self.config['models']['embeddings']['model_name']
        self.embedder = SentenceTransformer(model_name)
        
        # Paths
        self.resumes_path = Path(self.config['paths']['resumes'])
        self.vectorstore_path = Path(self.config['paths']['vectorstore'])
        
        # Create directories if they don't exist
        self.resumes_path.mkdir(parents=True, exist_ok=True)
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                # Try pdfplumber first (better for complex layouts)
                with pdfplumber.open(file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    
                if text.strip():
                    return text
                
                # Fallback to PyPDF2
                file.seek(0)
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(docx_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {docx_path}: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return self.extract_text_from_pdf(str(file_path))
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            return self.extract_text_from_docx(str(file_path))
        elif file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Unsupported file format: {file_path.suffix}")
            return ""
    
    def parse_resume_info(self, text: str) -> Dict[str, Any]:
        """Extract structured information from resume text"""
        info = {
            'skills': [],
            'experience_years': 0,
            'education': [],
            'companies': [],
            'technologies': [],
            'certifications': []
        }
        
        # Extract skills (common programming languages and technologies)
        skill_patterns = [
            r'\b(Python|Java|JavaScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin)\b',
            r'\b(React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|Linux)\b',
            r'\b(SQL|MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b',
            r'\b(Machine Learning|AI|Data Science|Deep Learning|NLP)\b'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            info['skills'].extend([match.lower() for match in matches])
        
        # Remove duplicates
        info['skills'] = list(set(info['skills']))
        
        # Extract experience years (simple heuristic)
        exp_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience\s*:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*in\s*(?:software|development|programming)'
        ]
        
        years = []
        for pattern in exp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            years.extend([int(match) for match in matches])
        
        if years:
            info['experience_years'] = max(years)
        
        # Extract education
        edu_patterns = [
            r'\b(Bachelor|Master|PhD|B\.Tech|M\.Tech|B\.Sc|M\.Sc|MBA)\b',
            r'\b(Computer Science|Software Engineering|Information Technology)\b'
        ]
        
        for pattern in edu_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            info['education'].extend(matches)
        
        return info
    
    def calculate_job_match_score(self, resume_info: Dict[str, Any], job_requirements: Dict[str, Any]) -> float:
        """Calculate how well a resume matches job requirements"""
        score = 0.0
        max_score = 0.0
        
        # Skills matching
        required_skills = [skill.lower() for skill in job_requirements.get('required_skills', [])]
        preferred_skills = [skill.lower() for skill in job_requirements.get('preferred_skills', [])]
        resume_skills = [skill.lower() for skill in resume_info.get('skills', [])]
        
        # Required skills (higher weight)
        if required_skills:
            required_matches = len(set(required_skills) & set(resume_skills))
            score += (required_matches / len(required_skills)) * 40
        max_score += 40
        
        # Preferred skills
        if preferred_skills:
            preferred_matches = len(set(preferred_skills) & set(resume_skills))
            score += (preferred_matches / len(preferred_skills)) * 20
        max_score += 20
        
        # Experience matching
        min_experience = job_requirements.get('min_experience_years', 0)
        candidate_experience = resume_info.get('experience_years', 0)
        
        if candidate_experience >= min_experience:
            # Bonus for more experience, but with diminishing returns
            exp_score = min(30, 20 + min(10, candidate_experience - min_experience))
            score += exp_score
        else:
            # Penalty for insufficient experience
            score += max(0, 20 - (min_experience - candidate_experience) * 5)
        max_score += 30
        
        # Education matching
        required_education = job_requirements.get('education_level', '').lower()
        candidate_education = ' '.join(resume_info.get('education', [])).lower()
        
        if required_education and required_education in candidate_education:
            score += 10
        max_score += 10
        
        return (score / max_score) * 100 if max_score > 0 else 0
    
    def filter_resumes(self, job_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter and rank resumes based on job requirements"""
        candidates = []
        
        # Process all resume files
        for file_path in self.resumes_path.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt']:
                logger.info(f"Processing resume: {file_path.name}")
                
                # Extract text
                text = self.extract_text_from_file(str(file_path))
                if not text.strip():
                    logger.warning(f"No text extracted from {file_path.name}")
                    continue
                
                # Parse resume information
                resume_info = self.parse_resume_info(text)
                
                # Calculate match score
                match_score = self.calculate_job_match_score(resume_info, job_requirements)
                
                # Create candidate record
                candidate = {
                    'filename': file_path.name,
                    'file_path': str(file_path),
                    'text': text[:1000] + "..." if len(text) > 1000 else text,  # Truncate for storage
                    'full_text': text,
                    'parsed_info': resume_info,
                    'match_score': round(match_score, 2),
                    'status': 'pending'
                }
                
                candidates.append(candidate)
        
        # Sort by match score (descending)
        candidates.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add ranking
        for i, candidate in enumerate(candidates):
            candidate['rank'] = i + 1
            candidate['recommendation'] = self._get_recommendation(candidate['match_score'])
        
        return candidates
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on match score"""
        if score >= 80:
            return "Highly Recommended"
        elif score >= 65:
            return "Recommended"
        elif score >= 50:
            return "Consider"
        else:
            return "Not Recommended"
    
    def save_filtered_results(self, candidates: List[Dict[str, Any]], output_path: str = None):
        """Save filtered results to JSON file"""
        if output_path is None:
            output_path = "frontend/streamlit_app/candidates.json"
        
        # Remove full_text from saved data to reduce file size
        candidates_to_save = []
        for candidate in candidates:
            candidate_copy = candidate.copy()
            candidate_copy.pop('full_text', None)  # Remove full text to save space
            candidates_to_save.append(candidate_copy)
        
        with open(output_path, 'w') as f:
            json.dump(candidates_to_save, f, indent=2)
        
        logger.info(f"Filtered results saved to {output_path}")
        return output_path
