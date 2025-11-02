"""
LLM-based Resume Parser
Uses Multi-Provider LLM (Ollama Cloud + Google Gemini) to parse resume text into structured JSON.
Validates the returned JSON using Pydantic schemas and generates 768-dim embeddings using JobBERT-v3.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from datetime import datetime
import numpy as np

from app.core.config import settings
from app.schemas.resume_schema import ResumeParseResult
from app.services.llm_provider import get_llm_service, LLMOptions
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class LLMResumeParser:
    """Parser that uses Multi-Provider LLM to produce structured JSON from resumes."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.embedding_service = get_embedding_service()
        
        logger.info("LLM Resume Parser initialized with multi-provider LLM and JobBERT-v3 (768-dim)")

    def _extract_text_from_pdf(self, file_path: str) -> str:
        try:
            # Lazy import to avoid top-level dependency errors during import-time checks
            import PyPDF2

            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page in reader.pages:
                    txt = page.extract_text() or ""
                    text.append(txt)
                return "\n".join(text).strip()
        except Exception as e:
            logger.error("PDF text extraction failed: %s", e)
            raise

    def _extract_text_from_docx(self, file_path: str) -> str:
        try:
            # Lazy import to avoid top-level dependency errors during import-time checks
            import docx

            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error("DOCX text extraction failed: %s", e)
            raise

    def _extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self._extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def generate_embeddings(self, text: str) -> tuple[np.ndarray, np.ndarray]:
        """
        Generate 768-dim embeddings using JobBERT-v3.
        Returns (resume_embedding, skills_embedding) as numpy arrays.
        """
        resume_emb_list = self.embedding_service.generate_text_embedding(text)
        skills_emb_list = self.embedding_service.generate_text_embedding(text)
        
        # Convert lists to numpy arrays
        resume_emb = np.array(resume_emb_list)
        skills_emb = np.array(skills_emb_list)
        
        return resume_emb, skills_emb

    def _build_prompt(self, text: str) -> str:
        """Construct a prompt instructing the model to return strict JSON matching the schema."""
        prompt = f"""
You are an expert resume parser. Given the full text of a candidate's resume (delimited below), extract structured information and return ONLY valid JSON. The JSON must follow this format exactly (fields may be null or empty lists):

{{
  "email": "...",
  "phone": "...",
  "full_name": "...",
  "location": "...",
  "skills": {{
    "technical": ["skill1", "skill2"],
    "soft": ["skill1", "skill2"]
  }},
  "education": [{{"degree":"...","university":"...","start_date":"...","end_date":"...","details":"..."}}],
  "work_experience": [{{"company":"...","title":"...","start_date":"...","end_date":"...","location":"...","description":"..."}}],
  "certifications": ["cert1"],
  "languages": ["English"],
  "resume_embedding": null,
  "skills_embedding": null,
  "raw_text": null,
  "parsed_at": null,
  "total_experience_years": null
}}

INSTRUCTIONS:
1) Parse the resume TEXT exactly once (do NOT hallucinate). Use the resume text below.
2) Return ONLY valid JSON. Do not include any explanation, commentary, or extra text.
3) Keep lists concise but include the key items (top technical skills, degrees, and 2-3 most recent roles).
4) If a field is not present, set it to null or an empty list as appropriate.

Resume Text:
"""
        # include only first ~6000 chars to keep prompt size reasonable
        max_chars = 6000
        snippet = text[:max_chars]
        prompt += snippet
        prompt += "\n\nReturn the JSON now.\n"
        return prompt

    async def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a resume file and return a validated dict matching ResumeParseResult.
        Uses Multi-Provider LLM with automatic failover.
        """
        logger.info("LLMResumeParser.parse called for %s", file_path)

        text = self._extract_text(file_path)
        if not text or len(text) < 50:
            raise ValueError("Extracted text is too short or empty")

        prompt = self._build_prompt(text)

        try:
            # Use Multi-Provider LLM service with automatic failover
            options = LLMOptions(
                temperature=0.1,
                max_tokens=1500,
                response_format="json"
            )
            
            llm_response = await self.llm_service.generate(prompt, options)
            
            if not llm_response or not llm_response.content:
                raise ValueError("Empty response from LLM")
            
            logger.info(f"Resume parsed using {llm_response.provider}")
            
            response_text = llm_response.content

            # Extract JSON substring
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start == -1 or end == -1:
                raise ValueError("Response from LLM did not contain JSON")

            json_str = response_text[start:end+1]
            parsed = json.loads(json_str)

            # Ensure important keys exist
            if 'skills' not in parsed:
                parsed['skills'] = {'technical': [], 'soft': []}

            # Attach raw_text and parsed_at if missing
            parsed.setdefault('raw_text', text)
            parsed.setdefault('parsed_at', datetime.utcnow().isoformat())

            # Validate via Pydantic schema
            try:
                validated = ResumeParseResult.model_validate(parsed)
            except Exception as e:
                logger.error("Validation failed for LLM output: %s", e)
                raise ValueError(f"LLM output validation failed: {e}")

            parsed_data = validated.model_dump()

            # Generate 768-dim JobBERT-v3 embeddings if missing
            if not parsed_data.get('resume_embedding'):
                resume_emb, skills_emb = self.generate_embeddings(parsed_data.get('raw_text', text))
                parsed_data['resume_embedding'] = resume_emb.tolist()
                parsed_data['skills_embedding'] = skills_emb.tolist()

            logger.info(f"Resume parsed successfully with 768-dim embeddings (provider: {llm_response.provider})")
            return parsed_data

        except Exception as e:
            logger.error("LLM parser failed: %s", e, exc_info=True)
            # Fallback: return basic contact extraction and embeddings
            fallback = {
                'email': None,
                'phone': None,
                'full_name': None,
                'location': None,
                'skills': {'technical': [], 'soft': []},
                'education': [],
                'work_experience': [],
                'certifications': [],
                'languages': [],
                'raw_text': text,
                'parsed_at': datetime.utcnow().isoformat(),
                'total_experience_years': None
            }

            # Try to extract email and phone via regex
            email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
            phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
            if email_match:
                fallback['email'] = email_match.group(0)
            if phone_match:
                fallback['phone'] = phone_match.group(0)

            try:
                resume_emb, skills_emb = self.generate_embeddings(text)
                fallback['resume_embedding'] = resume_emb.tolist()
                fallback['skills_embedding'] = skills_emb.tolist()
            except Exception:
                fallback['resume_embedding'] = None
                fallback['skills_embedding'] = None

            logger.warning("Returning fallback resume parse with basic info")
            return fallback
