"""
Resume Parser Service
Extracts information from PDF/DOCX resumes using spaCy NER and sentence-transformers.
Generates 384-dimensional embeddings for semantic search.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# PDF/DOCX extraction
import PyPDF2
import docx

# NLP and embeddings
import spacy
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Parses resumes to extract structured data and generate embeddings.
    
    Uses:
    - spaCy (en_core_web_lg) for Named Entity Recognition
    - sentence-transformers/all-MiniLM-L6-v2 for general embeddings
    - anass1209/resume-job-matcher-all-MiniLM-L6-v2 for job matching
    """
    
    def __init__(self):
        """Initialize NLP models (may take 30-60 seconds on first run)."""
        logger.info("Loading spaCy model...")
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            logger.error("spaCy model 'en_core_web_lg' not found. Run: python -m spacy download en_core_web_lg")
            raise
        
        logger.info("Loading sentence-transformers embedding model...")
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        logger.info("Loading resume-job matcher model...")
        self.matching_model = SentenceTransformer('anass1209/resume-job-matcher-all-MiniLM-L6-v2')
        
        logger.info("All models loaded successfully")
        
        # Common skill keywords (can be expanded)
        self.technical_skills = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'fastapi',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform',
            'git', 'jenkins', 'ci/cd', 'agile', 'scrum',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'
        }
        
        self.soft_skills = {
            'leadership', 'communication', 'teamwork', 'problem solving',
            'critical thinking', 'time management', 'adaptability', 'creativity'
        }
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            raise
    
    def extract_text(self, file_path: str) -> str:
        """Auto-detect file type and extract text."""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address using regex."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number using regex."""
        # Matches formats: (123) 456-7890, 123-456-7890, 123.456.7890, +1 123 456 7890
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else None
    
    def extract_entities_spacy(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy NER."""
        doc = self.nlp(text)
        
        entities = {
            'organizations': [],  # Companies worked at
            'locations': [],
            'dates': [],
            'persons': []  # Might catch candidate name
        }
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ in ['GPE', 'LOC']:  # Geographic/Location
                entities['locations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'PERSON':
                entities['persons'].append(ent.text)
        
        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical and soft skills from text."""
        text_lower = text.lower()
        
        found_technical = []
        found_soft = []
        
        # Technical skills
        for skill in self.technical_skills:
            if skill in text_lower:
                found_technical.append(skill)
        
        # Soft skills
        for skill in self.soft_skills:
            if skill in text_lower:
                found_soft.append(skill)
        
        return {
            'technical_skills': found_technical,
            'soft_skills': found_soft
        }
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information (basic regex-based)."""
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'(bachelor|master|phd|doctorate|associate|b\.?s\.?|m\.?s\.?|m\.?b\.?a\.?|ph\.?d\.?)',
            r'(computer science|engineering|business|mathematics|physics|chemistry)'
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains degree keywords
            for pattern in degree_patterns:
                if re.search(pattern, line_lower):
                    # Try to extract university name from nearby lines
                    university = lines[i+1] if i+1 < len(lines) else ""
                    
                    education.append({
                        'degree': line.strip(),
                        'university': university.strip()
                    })
                    break
        
        return education
    
    def extract_work_experience(self, text: str, entities: Dict) -> List[Dict[str, str]]:
        """Extract work experience using organizations and dates."""
        experiences = []
        
        # Simple heuristic: pair organizations with nearby dates
        orgs = entities.get('organizations', [])
        dates = entities.get('dates', [])
        
        for org in orgs[:5]:  # Limit to top 5 organizations
            experiences.append({
                'company': org,
                'dates': ', '.join(dates[:2]) if dates else 'Unknown'  # Use first 2 dates found
            })
        
        return experiences
    
    def generate_embeddings(self, text: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate embeddings for resume text.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (resume_embedding, skills_embedding)
        """
        # Full resume embedding (384 dimensions)
        resume_embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        
        # Skills-focused embedding (extract skills section for better matching)
        # For now, use full text for both (can be optimized later)
        skills_embedding = self.matching_model.encode(text, convert_to_numpy=True)
        
        return resume_embedding, skills_embedding
    
    def parse(self, file_path: str) -> Dict:
        """
        Main parsing method - orchestrates all extraction steps.
        
        Args:
            file_path: Path to PDF or DOCX resume file
            
        Returns:
            Dict with parsed resume data including embeddings
        """
        logger.info(f"Parsing resume: {file_path}")
        
        # 1. Extract text
        text = self.extract_text(file_path)
        
        if not text or len(text) < 50:
            raise ValueError("Extracted text is too short or empty")
        
        # 2. Extract basic info
        email = self.extract_email(text)
        phone = self.extract_phone(text)
        
        # 3. NER extraction
        entities = self.extract_entities_spacy(text)
        
        # 4. Skills extraction
        skills_dict = self.extract_skills(text)
        
        # 5. Education extraction
        education = self.extract_education(text)
        
        # 6. Work experience extraction
        work_experience = self.extract_work_experience(text, entities)
        
        # 7. Generate embeddings
        resume_embedding, skills_embedding = self.generate_embeddings(text)
        
        # 8. Compile results
        parsed_data = {
            'email': email,
            'phone': phone,
            'full_name': entities['persons'][0] if entities['persons'] else None,
            'location': entities['locations'][0] if entities['locations'] else None,
            
            # JSONB fields
            'skills': {
                'technical': skills_dict['technical_skills'],
                'soft': skills_dict['soft_skills']
            },
            'education': education,
            'work_experience': work_experience,
            
            # Vector embeddings (384 dimensions each)
            'resume_embedding': resume_embedding.tolist(),  # Convert numpy to list for JSON
            'skills_embedding': skills_embedding.tolist(),
            
            # Metadata
            'raw_text': text,
            'parsed_at': datetime.utcnow().isoformat(),
            'total_experience_years': len(work_experience),  # Rough estimate
        }
        
        logger.info(f"Resume parsed successfully. Email: {email}, Skills: {len(skills_dict['technical_skills'])}")
        
        return parsed_data


# Singleton instance (lazy-loaded)
_parser_instance: Optional[ResumeParser] = None


def get_resume_parser() -> ResumeParser:
    """
    Get singleton instance of ResumeParser.
    Models are loaded only once on first call.
    """
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ResumeParser()
    return _parser_instance
