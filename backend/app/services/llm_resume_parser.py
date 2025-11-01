"""
LLM-based Resume Parser
Uses local Ollama (configurable via settings) to parse resume text into structured JSON.
Validates the returned JSON using Pydantic schemas and generates embeddings using
sentence-transformers when embeddings are not provided by the LLM.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from datetime import datetime
import numpy as np  # kept for typing/usage; import moved into __init__ if necessary

from app.core.config import settings
from app.schemas.resume_schema import ResumeParseResult

logger = logging.getLogger(__name__)


class LLMResumeParser:
    """Parser that uses a local Ollama model to produce structured JSON from resumes."""

    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_cloud_url = settings.OLLAMA_CLOUD_URL
        self.ollama_api_key = settings.OLLAMA_API_KEY
        self.model = settings.OLLAMA_MODEL
        self.embedding_model_name = settings.SENTENCE_TRANSFORMER_MODEL
        self.use_cloud = bool(self.ollama_api_key)  # Use cloud if API key is set

        logger.info("Loading sentence-transformers model for embeddings: %s", self.embedding_model_name)
        if self.use_cloud:
            logger.info("Using Ollama Cloud API with model: %s", self.model)
        else:
            logger.info("Using local Ollama at %s with model: %s", self.ollama_host, self.model)
        
        try:
            # Lazy import heavy dependency
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer(self.embedding_model_name)
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            raise

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

    def generate_embeddings(self, text: str) -> (np.ndarray, np.ndarray):
        """Return (resume_embedding, skills_embedding) as numpy arrays."""
        resume_emb = self.embedding_model.encode(text, convert_to_numpy=True)
        skills_emb = self.embedding_model.encode(text, convert_to_numpy=True)
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

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a resume file and return a validated dict matching ResumeParseResult."""
        logger.info("LLMResumeParser.parse called for %s", file_path)

        text = self._extract_text(file_path)
        if not text or len(text) < 50:
            raise ValueError("Extracted text is too short or empty")

        prompt = self._build_prompt(text)

        try:
            # Build generate endpoint & headers for local/cloud
            if self.use_cloud:
                # If cloud URL already contains an API path (e.g., /api/ or /v1/...), use it as-is.
                base = self.ollama_cloud_url.rstrip('/')
                if any(p in base for p in ['/api', '/v1', '/generate', '/completions', '/tags']):
                    generate_url = base
                else:
                    generate_url = f"{base}/api/generate"
                headers = {
                    "Authorization": f"Bearer {self.ollama_api_key}",
                    "Content-Type": "application/json",
                }
            else:
                generate_url = f"{self.ollama_host.rstrip('/')}/api/generate"
                headers = None

            with httpx.Client(timeout=60.0, headers=headers) as client:
                response = client.post(
                    generate_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1, "num_predict": 1500}
                    },
                )

            if response.status_code != 200:
                # Include body for diagnostics (do not log API keys)
                body = None
                try:
                    body = response.text
                except Exception:
                    body = "<unavailable>"
                logger.error("Ollama responded with status %s: %s", response.status_code, body)
                raise RuntimeError(f"Ollama API error: {response.status_code} - {body}")

            result = response.json()

            # Try a few common response shapes to extract the assistant text
            response_text = ""
            if isinstance(result, dict):
                # Local Ollama style
                response_text = result.get("response") or ""
                # Ollama Cloud / OpenAI-style
                if not response_text:
                    # SDK-like message
                    msg = result.get("message")
                    if isinstance(msg, dict):
                        response_text = msg.get("content", "")
                if not response_text:
                    # openai-style choices
                    choices = result.get("choices")
                    if isinstance(choices, list) and len(choices) > 0:
                        first = choices[0]
                        if isinstance(first, dict):
                            # nested message content
                            response_text = (first.get("message", {}) or {}).get("content") or first.get("text") or ""
            elif isinstance(result, str):
                response_text = result
            else:
                response_text = str(result)

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

            # If embeddings missing, compute them
            if not parsed_data.get('resume_embedding'):
                resume_emb, skills_emb = self.generate_embeddings(parsed_data.get('raw_text', text))
                parsed_data['resume_embedding'] = resume_emb.tolist()
                parsed_data['skills_embedding'] = skills_emb.tolist()

            return parsed_data

        except Exception as e:
            logger.error("LLM parser failed: %s", e, exc_info=True)
            # As a minimal fallback, try to return basic contact extraction and embeddings
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

            return fallback
