"""
Company Knowledge API Endpoints
Manages company-specific knowledge for RAG-powered context-aware screening
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_, func
import time

from app.db.database import get_db
from app.models.company_knowledge import CompanyKnowledge
from app.models.organization import Organization
from app.schemas.company_knowledge import (
    CompanyKnowledgeCreate,
    CompanyKnowledgeUpdate,
    CompanyKnowledgeResponse,
    CompanyKnowledgeListResponse,
    CompanyKnowledgeSearchRequest,
    CompanyKnowledgeSearchResponse,
    CompanyKnowledgeSearchResult,
    CompanyKnowledgeBulkCreateRequest,
    CompanyKnowledgeBulkCreateResponse,
    CompanyKnowledgeStats,
    DocumentType
)
from app.services.rag_service import RAGService
from app.services.embedding_service import EmbeddingService

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["Company Knowledge"])

# Initialize services (singleton pattern)
embedding_service = EmbeddingService()
rag_service = RAGService(embedding_service)


@router.post("/", response_model=CompanyKnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_document(
    doc_data: CompanyKnowledgeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new company knowledge document with automatic embedding generation.
    
    - **doc_type**: Type of document (company_values, tech_requirements, etc.)
    - **title**: Document title
    - **content**: Document content (min 10 chars, max 10k chars)
    - **metadata**: Optional metadata (tags, priority, etc.)
    - **organization_id**: Organization ID (defaults to 1 if not provided)
    """
    try:
        # Default to organization_id=1 if not provided (for testing)
        org_id = doc_data.organization_id or 1
        
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {org_id} not found"
            )
        
        # Store document using RAG service (generates embedding automatically)
        doc_id = await rag_service.store_document(
            db=db,
            content=doc_data.content,
            doc_type=doc_data.doc_type.value,
            organization_id=org_id,
            title=doc_data.title,
            metadata=doc_data.metadata or {}
        )
        
        # Retrieve and return the created document
        document = db.query(CompanyKnowledge).filter(CompanyKnowledge.id == doc_id).first()
        
        logger.info(f"Created knowledge document {doc_id}: {doc_data.title} (org={org_id}, type={doc_data.doc_type})")
        
        return CompanyKnowledgeResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating knowledge document: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge document: {str(e)}"
        )


@router.get("/", response_model=CompanyKnowledgeListResponse)
def list_knowledge_documents(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    doc_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|title|doc_type)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    List company knowledge documents with filtering, searching, and pagination.
    
    - **organization_id**: Filter by organization (default: all)
    - **doc_type**: Filter by document type
    - **search**: Search in title and content
    - **page**: Page number (starts at 1)
    - **per_page**: Results per page (1-100)
    - **sort_by**: Sort field (created_at, updated_at, title, doc_type)
    - **sort_order**: Sort direction (asc, desc)
    """
    try:
        query = db.query(CompanyKnowledge)
        
        # Apply filters
        if organization_id:
            query = query.filter(CompanyKnowledge.organization_id == organization_id)
        
        if doc_type:
            query = query.filter(CompanyKnowledge.doc_type == doc_type.value)
        
        if search:
            search_filter = or_(
                CompanyKnowledge.title.ilike(f"%{search}%"),
                CompanyKnowledge.content.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(CompanyKnowledge, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * per_page
        documents = query.offset(offset).limit(per_page).all()
        
        # Calculate pagination metadata
        has_next = (offset + per_page) < total
        has_prev = page > 1
        
        return CompanyKnowledgeListResponse(
            documents=[CompanyKnowledgeResponse.from_orm(doc) for doc in documents],
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Error listing knowledge documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=CompanyKnowledgeResponse)
def get_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific company knowledge document by ID.
    """
    document = db.query(CompanyKnowledge).filter(CompanyKnowledge.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document {document_id} not found"
        )
    
    return CompanyKnowledgeResponse.from_orm(document)


@router.post("/search", response_model=CompanyKnowledgeSearchResponse)
async def search_knowledge(
    search_request: CompanyKnowledgeSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform semantic search across company knowledge documents using RAG.
    
    - **query**: Search query (min 3 chars)
    - **doc_types**: Filter by document types (optional)
    - **top_k**: Number of results (1-20, default 5)
    - **similarity_threshold**: Minimum similarity score (0-1, default 0.2)
    - **organization_id**: Organization ID (defaults to 1 if not provided)
    
    Returns documents ranked by cosine similarity with the query.
    """
    try:
        start_time = time.time()
        
        # Default to organization_id=1 if not provided (for testing)
        org_id = search_request.organization_id or 1
        
        # Convert doc_types to list of strings if provided
        doc_types = [dt.value for dt in search_request.doc_types] if search_request.doc_types else None
        
        # Perform similarity search using RAG service
        results = await rag_service.similarity_search(
            db=db,
            query=search_request.query,
            organization_id=org_id,
            doc_types=doc_types,
            top_k=search_request.top_k,
            threshold=search_request.similarity_threshold  # Fixed parameter name
        )
        
        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000
        
        # Convert results to response schema
        search_results = [
            CompanyKnowledgeSearchResult(
                id=result["id"],
                organization_id=result["organization_id"],
                doc_type=result["doc_type"],
                title=result["title"],
                content=result["content"],
                metadata=result["metadata"],
                similarity_score=result["similarity"],
                created_at=result["created_at"]
            )
            for result in results
        ]
        
        logger.info(
            f"Knowledge search: query='{search_request.query}', "
            f"org={org_id}, results={len(search_results)}, time={search_time_ms:.1f}ms"
        )
        
        return CompanyKnowledgeSearchResponse(
            query=search_request.query,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=round(search_time_ms, 2)
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge: {str(e)}"
        )


@router.put("/{document_id}", response_model=CompanyKnowledgeResponse)
def update_knowledge_document(
    document_id: int,
    doc_update: CompanyKnowledgeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing company knowledge document.
    
    If content is updated, embeddings are automatically regenerated.
    """
    try:
        # Verify document exists
        document = db.query(CompanyKnowledge).filter(CompanyKnowledge.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document {document_id} not found"
            )
        
        # Track if content changed (need to regenerate embeddings)
        content_changed = False
        update_data = doc_update.dict(exclude_unset=True)
        
        # Update fields
        for field, value in update_data.items():
            if field == "content" and value != document.content:
                content_changed = True
            
            if field == "doc_type":
                setattr(document, field, value.value if hasattr(value, 'value') else value)
            elif field == "metadata":
                # Update doc_metadata (actual column name)
                setattr(document, "doc_metadata", value)
            else:
                setattr(document, field, value)
        
        # Regenerate embeddings if content changed
        if content_changed:
            logger.info(f"Regenerating embeddings for document {document_id} (content changed)")
            embedding = embedding_service.generate_text_embedding(document.content)
            document.embedding = embedding
        
        db.commit()
        db.refresh(document)
        
        logger.info(f"Updated knowledge document {document_id}: {document.title}")
        
        return CompanyKnowledgeResponse.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge document {document_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update knowledge document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a company knowledge document permanently.
    """
    try:
        document = db.query(CompanyKnowledge).filter(CompanyKnowledge.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document {document_id} not found"
            )
        
        db.delete(document)
        db.commit()
        
        logger.info(f"Deleted knowledge document {document_id}: {document.title}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge document {document_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge document: {str(e)}"
        )


@router.post("/bulk", response_model=CompanyKnowledgeBulkCreateResponse)
async def bulk_create_knowledge(
    bulk_request: CompanyKnowledgeBulkCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk create multiple company knowledge documents at once (max 50).
    
    Useful for initial setup or importing large knowledge bases.
    """
    try:
        created_ids = []
        errors = []
        org_id = bulk_request.organization_id or 1
        
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {org_id} not found"
            )
        
        for idx, doc_data in enumerate(bulk_request.documents):
            try:
                doc_id = await rag_service.store_document(
                    db=db,
                    content=doc_data.content,
                    doc_type=doc_data.doc_type.value,
                    organization_id=org_id,
                    title=doc_data.title,
                    metadata=doc_data.metadata or {}
                )
                created_ids.append(doc_id)
            except Exception as e:
                errors.append({
                    "index": idx,
                    "title": doc_data.title,
                    "error": str(e)
                })
                logger.error(f"Failed to create document '{doc_data.title}': {str(e)}")
        
        db.commit()
        
        logger.info(
            f"Bulk created knowledge documents: "
            f"created={len(created_ids)}, failed={len(errors)}, org={org_id}"
        )
        
        return CompanyKnowledgeBulkCreateResponse(
            created=len(created_ids),
            failed=len(errors),
            document_ids=created_ids,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk knowledge creation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create knowledge documents: {str(e)}"
        )


@router.get("/stats/{organization_id}", response_model=CompanyKnowledgeStats)
def get_knowledge_stats(
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Get statistics about an organization's knowledge base.
    
    - Total documents
    - Documents by type
    - Content length statistics
    - Last updated timestamp
    """
    try:
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )
        
        # Get total documents
        total_docs = db.query(CompanyKnowledge).filter(
            CompanyKnowledge.organization_id == organization_id
        ).count()
        
        # Get documents by type
        docs_by_type_query = db.query(
            CompanyKnowledge.doc_type,
            func.count(CompanyKnowledge.id)
        ).filter(
            CompanyKnowledge.organization_id == organization_id
        ).group_by(CompanyKnowledge.doc_type).all()
        
        docs_by_type = {doc_type: count for doc_type, count in docs_by_type_query}
        
        # Get content length statistics
        content_stats = db.query(
            func.sum(func.length(CompanyKnowledge.content)).label('total_length'),
            func.avg(func.length(CompanyKnowledge.content)).label('avg_length')
        ).filter(
            CompanyKnowledge.organization_id == organization_id
        ).first()
        
        total_content_length = content_stats.total_length or 0
        average_content_length = float(content_stats.avg_length or 0)
        
        # Get last updated timestamp
        last_doc = db.query(CompanyKnowledge).filter(
            CompanyKnowledge.organization_id == organization_id
        ).order_by(desc(CompanyKnowledge.updated_at)).first()
        
        last_updated = last_doc.updated_at if last_doc else None
        
        return CompanyKnowledgeStats(
            organization_id=organization_id,
            total_documents=total_docs,
            documents_by_type=docs_by_type,
            total_content_length=total_content_length,
            average_content_length=round(average_content_length, 1),
            last_updated=last_updated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge stats for org {organization_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge stats: {str(e)}"
        )
