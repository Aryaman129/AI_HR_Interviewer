"""
Embedding Service using TechWolf JobBERT-v3

This service provides high-quality job-specific embeddings using the JobBERT-v3 model
from TechWolf. JobBERT-v3 is specifically trained on job descriptions and resumes,
providing 10-15% better accuracy than general-purpose models like MiniLM.

Key Features:
- 768-dimensional embeddings (BERT-base architecture)
- Job-specific vocabulary and context understanding
- Better understanding of technical skills and job requirements
- Optimized for HR/recruitment use cases

Model: TechWolf/JobBERT-v3
Dimensions: 768 (BERT-base)
Use Cases: Job descriptions, resumes, skills matching, candidate ranking
"""

from typing import List, Optional
import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating job-specific embeddings using JobBERT-v3.
    
    This service uses a singleton pattern with LRU caching to avoid
    loading the model multiple times, which would consume excessive memory.
    """
    
    _instance: Optional['EmbeddingService'] = None
    _model: Optional[SentenceTransformer] = None
    _embedding_dim: Optional[int] = None
    
    MODEL_NAME = "TechWolf/JobBERT-v3"
    EXPECTED_DIMENSION = 768  # JobBERT-v3 actually outputs 768-dim (BERT-base)
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding service (loads model on first call)."""
        if self._model is None:
            logger.info(f"Loading JobBERT-v3 model: {self.MODEL_NAME}")
            try:
                self._model = SentenceTransformer(self.MODEL_NAME)
                # Get actual embedding dimension from model
                test_emb = self._model.encode("test", convert_to_numpy=True)
                self._embedding_dim = len(test_emb)
                logger.info(f"✓ Model loaded successfully. Embedding dimension: {self._embedding_dim}")
            except Exception as e:
                logger.error(f"Failed to load JobBERT-v3 model: {e}")
                raise RuntimeError(f"Could not initialize embedding service: {e}")
    
    @property
    def EMBEDDING_DIMENSION(self) -> int:
        """Get the actual embedding dimension from the model."""
        return self._embedding_dim if self._embedding_dim is not None else self.EXPECTED_DIMENSION
    
    def generate_resume_embedding(
        self, 
        resume_text: str,
        include_skills: Optional[str] = None,
        include_experience: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a resume.
        
        Args:
            resume_text: The full resume text
            include_skills: Optional skills summary to emphasize
            include_experience: Optional experience summary to emphasize
            
        Returns:
            List of 1024 floats representing the embedding
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_resume_embedding(
            ...     resume_text="Experienced Python developer...",
            ...     include_skills="Python, FastAPI, PostgreSQL"
            ... )
            >>> len(embedding)
            1024
        """
        # Construct weighted text for better embeddings
        text_parts = [resume_text]
        
        if include_skills:
            # Give more weight to skills by repeating
            text_parts.append(f"Key Skills: {include_skills}")
        
        if include_experience:
            text_parts.append(f"Experience: {include_experience}")
        
        combined_text = " | ".join(text_parts)
        
        return self._generate_embedding(combined_text, "resume")
    
    def generate_job_embedding(
        self,
        job_description: str,
        required_skills: Optional[str] = None,
        job_title: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a job description.
        
        Args:
            job_description: The full job description text
            required_skills: Optional required skills to emphasize
            job_title: Optional job title to emphasize
            
        Returns:
            List of 1024 floats representing the embedding
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_job_embedding(
            ...     job_description="We are looking for a senior backend engineer...",
            ...     required_skills="Python, FastAPI, Docker",
            ...     job_title="Senior Backend Engineer"
            ... )
            >>> len(embedding)
            1024
        """
        # Construct weighted text for better embeddings
        text_parts = []
        
        if job_title:
            # Job title is very important for matching
            text_parts.append(f"Job Title: {job_title}")
        
        text_parts.append(job_description)
        
        if required_skills:
            # Give more weight to required skills
            text_parts.append(f"Required Skills: {required_skills}")
        
        combined_text = " | ".join(text_parts)
        
        return self._generate_embedding(combined_text, "job")
    
    def generate_text_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for arbitrary text.
        
        This is useful for company knowledge base documents, interview questions,
        or any other text that needs to be embedded for semantic search.
        
        Args:
            text: The text to embed
            
        Returns:
            List of 1024 floats representing the embedding
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_text_embedding(
            ...     "Our company values diversity and innovation"
            ... )
            >>> len(embedding)
            1024
        """
        return self._generate_embedding(text, "text")
    
    def generate_skills_embedding(self, skills: List[str]) -> List[float]:
        """
        Generate embedding for a list of skills.
        
        Args:
            skills: List of skill names
            
        Returns:
            List of 1024 floats representing the embedding
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = service.generate_skills_embedding(
            ...     ["Python", "FastAPI", "PostgreSQL", "Docker"]
            ... )
            >>> len(embedding)
            1024
        """
        # Join skills with commas for natural language processing
        skills_text = ", ".join(skills)
        return self._generate_embedding(skills_text, "skills")
    
    def _generate_embedding(self, text: str, text_type: str = "general") -> List[float]:
        """
        Internal method to generate embeddings.
        
        Args:
            text: The text to embed
            text_type: Type of text (for logging purposes)
            
        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for {text_type} embedding, returning zero vector")
            return [0.0] * self.EMBEDDING_DIMENSION
        
        try:
            # Generate embedding
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            # Convert to list of floats
            embedding_list = embedding.tolist()
            
            logger.debug(
                f"Generated {text_type} embedding (dim={len(embedding_list)}, "
                f"norm={np.linalg.norm(embedding):.4f})"
            )
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating {text_type} embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a batch (more efficient).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (each embedding is a list of 1024 floats)
            
        Example:
            >>> service = EmbeddingService()
            >>> embeddings = service.batch_generate_embeddings([
            ...     "Python developer with 5 years experience",
            ...     "Senior data scientist seeking new opportunities"
            ... ])
            >>> len(embeddings)
            2
            >>> len(embeddings[0])
            1024
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return []
        
        try:
            # Filter out empty texts
            valid_texts = [t for t in texts if t and t.strip()]
            if len(valid_texts) != len(texts):
                logger.warning(
                    f"Filtered out {len(texts) - len(valid_texts)} empty texts from batch"
                )
            
            if not valid_texts:
                return [[0.0] * self.EMBEDDING_DIMENSION] * len(texts)
            
            # Generate embeddings in batch
            embeddings = self._model.encode(valid_texts, convert_to_numpy=True)
            
            # Convert to list of lists
            embeddings_list = [emb.tolist() for emb in embeddings]
            
            logger.info(f"Generated {len(embeddings_list)} embeddings in batch")
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            raise RuntimeError(f"Failed to generate batch embeddings: {e}")
    
    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1 (higher is more similar)
            
        Example:
            >>> service = EmbeddingService()
            >>> emb1 = service.generate_text_embedding("Python developer")
            >>> emb2 = service.generate_text_embedding("Software engineer")
            >>> similarity = service.cosine_similarity(emb1, emb2)
            >>> 0 <= similarity <= 1
            True
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)


# Global instance (singleton)
@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance.
    
    This function uses LRU cache to ensure we only create one instance.
    
    Returns:
        EmbeddingService instance
        
    Example:
        >>> service = get_embedding_service()
        >>> embedding = service.generate_text_embedding("Hello world")
    """
    return EmbeddingService()
