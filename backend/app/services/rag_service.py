"""
RAG Service for company-specific knowledge retrieval.

Provides document storage, similarity search, and prompt augmentation
using pgvector and JobBERT-v3 768-dimensional embeddings.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.models.company_knowledge import CompanyKnowledge
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for company knowledge.
    
    Features:
    - Store company documents with vector embeddings
    - Similarity search using pgvector HNSW index
    - Context-aware prompt augmentation for LLMs
    """
    
    def __init__(self, embedding_service: EmbeddingService):
        """Initialize RAG service with embedding provider."""
        self.embedding_service = embedding_service
    
    async def store_document(
        self,
        db: Session,
        content: str,
        doc_type: str,
        organization_id: int,
        title: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CompanyKnowledge:
        """
        Store a company document with vector embedding.
        
        Args:
            db: Database session
            content: Document text content
            doc_type: Type of document (company_values, tech_requirements, interview_style, etc.)
            organization_id: Organization ID
            title: Document title
            metadata: Optional metadata dict (tags, author, version, etc.)
        
        Returns:
            Created CompanyKnowledge instance
        
        Example:
            doc = await rag_service.store_document(
                db=db,
                content="We value innovation, collaboration, and continuous learning...",
                doc_type="company_values",
                organization_id=1,
                title="Core Company Values",
                metadata={"tags": ["culture", "hiring"], "author": "HR Team"}
            )
        """
        try:
            # Generate 768-dim embedding
            logger.info(f"Generating embedding for document: {title}")
            embedding = self.embedding_service.generate_text_embedding(content)
            
            # Create document
            doc = CompanyKnowledge(
                organization_id=organization_id,
                doc_type=doc_type,
                title=title,
                content=content,
                embedding=embedding,
                doc_metadata=metadata or {}
            )
            
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            logger.info(f"Stored document {doc.id} for org {organization_id}")
            return doc
            
        except Exception as e:
            logger.error(f"Failed to store document: {str(e)}")
            db.rollback()
            raise
    
    async def similarity_search(
        self,
        db: Session,
        query: str,
        organization_id: int,
        doc_types: Optional[List[str]] = None,
        top_k: int = 3,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using pgvector cosine similarity.
        
        Args:
            db: Database session
            query: Search query text
            organization_id: Filter by organization
            doc_types: Optional list of doc types to filter (e.g., ["company_values", "tech_requirements"])
            top_k: Number of results to return
            threshold: Minimum similarity score (0.0 to 1.0)
        
        Returns:
            List of dicts with {id, title, content, doc_type, similarity, metadata}
        
        Example:
            results = await rag_service.similarity_search(
                db=db,
                query="What are our core engineering principles?",
                organization_id=1,
                doc_types=["company_values", "tech_requirements"],
                top_k=5
            )
        """
        try:
            # Generate query embedding
            logger.info(f"Searching for: {query[:50]}...")
            query_embedding = self.embedding_service.generate_text_embedding(query)
            
            # Build SQL with pgvector similarity
            # Handle optional doc_types filter
            if doc_types:
                sql = text("""
                    SELECT 
                        id,
                        title,
                        content,
                        doc_type,
                        metadata,
                        1 - (embedding <=> :query_embedding) AS similarity
                    FROM company_knowledge
                    WHERE organization_id = :org_id
                        AND doc_type = ANY(:doc_types)
                        AND (1 - (embedding <=> :query_embedding)) >= :threshold
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :top_k
                """)
            else:
                sql = text("""
                    SELECT 
                        id,
                        title,
                        content,
                        doc_type,
                        metadata,
                        1 - (embedding <=> :query_embedding) AS similarity
                    FROM company_knowledge
                    WHERE organization_id = :org_id
                        AND (1 - (embedding <=> :query_embedding)) >= :threshold
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :top_k
                """)
            
            # Execute query with appropriate parameters
            params = {
                "query_embedding": str(query_embedding),
                "org_id": organization_id,
                "threshold": threshold,
                "top_k": top_k
            }
            if doc_types:
                params["doc_types"] = doc_types
            
            result = db.execute(sql, params)
            
            rows = result.fetchall()
            
            # Format results
            results = [
                {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "doc_type": row[3],
                    "metadata": row[4],
                    "similarity": float(row[5])
                }
                for row in rows
            ]
            
            logger.info(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise
    
    async def augment_prompt(
        self,
        db: Session,
        query: str,
        organization_id: int,
        context_types: Optional[List[str]] = None,
        max_context_tokens: int = 2000
    ) -> str:
        """
        Augment a prompt with relevant company context.
        
        Args:
            db: Database session
            query: Original query/prompt
            organization_id: Organization ID
            context_types: Types of context to retrieve (default: ["company_values", "tech_requirements"])
            max_context_tokens: Maximum tokens for context (rough estimate)
        
        Returns:
            Enhanced prompt with company context
        
        Example:
            enhanced_prompt = await rag_service.augment_prompt(
                db=db,
                query="Generate interview questions for a senior engineer",
                organization_id=1,
                context_types=["company_values", "tech_requirements", "interview_style"]
            )
        """
        try:
            # Default context types
            if context_types is None:
                context_types = ["company_values", "tech_requirements"]
            
            # Search for relevant documents
            results = await self.similarity_search(
                db=db,
                query=query,
                organization_id=organization_id,
                doc_types=context_types,
                top_k=5
            )
            
            if not results:
                logger.warning(f"No context found for org {organization_id}")
                return query  # Return original if no context
            
            # Build context string
            context_parts = []
            total_chars = 0
            max_chars = max_context_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
            
            for doc in results:
                doc_text = f"[{doc['doc_type']}] {doc['title']}\n{doc['content']}"
                
                if total_chars + len(doc_text) > max_chars:
                    break
                
                context_parts.append(doc_text)
                total_chars += len(doc_text)
            
            context = "\n\n".join(context_parts)
            
            # Construct enhanced prompt
            enhanced_prompt = f"""# Company Context

{context}

# Task

{query}

Please use the company context above to provide a response that aligns with our values, requirements, and style."""
            
            logger.info(f"Augmented prompt with {len(context_parts)} documents ({total_chars} chars)")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Prompt augmentation failed: {str(e)}")
            # Return original query on error
            return query
