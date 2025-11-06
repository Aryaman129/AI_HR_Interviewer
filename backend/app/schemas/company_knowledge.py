"""
Company Knowledge Pydantic schemas for API validation
Supports RAG-powered context-aware screening with company-specific knowledge
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Types of company knowledge documents"""
    COMPANY_VALUES = "company_values"
    TECH_REQUIREMENTS = "tech_requirements"
    INTERVIEW_STYLE = "interview_style"
    CULTURE = "culture"
    BENEFITS = "benefits"
    TEAM_STRUCTURE = "team_structure"
    PROJECT_INFO = "project_info"
    OTHER = "other"


class CompanyKnowledgeBase(BaseModel):
    """Base schema for company knowledge"""
    doc_type: DocumentType = Field(..., description="Type of knowledge document")
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=10, max_length=10000, description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata (tags, category, priority, etc.)"
    )
    
    @validator('content')
    def validate_content_length(cls, v):
        """Ensure content is meaningful"""
        if len(v.strip()) < 10:
            raise ValueError('Content must be at least 10 characters long')
        return v.strip()
    
    @validator('title')
    def validate_title(cls, v):
        """Ensure title is not empty"""
        if len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Ensure metadata is not too large"""
        if v and len(str(v)) > 5000:
            raise ValueError('Metadata too large (max 5000 chars)')
        return v


class CompanyKnowledgeCreate(CompanyKnowledgeBase):
    """Schema for creating a new company knowledge document"""
    organization_id: Optional[int] = Field(
        None,
        description="Organization ID (auto-detected from auth if not provided)"
    )


class CompanyKnowledgeUpdate(BaseModel):
    """Schema for updating an existing company knowledge document"""
    doc_type: Optional[DocumentType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=10, max_length=10000)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('content')
    def validate_content_length(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError('Content must be at least 10 characters long')
        return v.strip() if v else None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v.strip() if v else None


class CompanyKnowledgeResponse(BaseModel):
    """Schema for company knowledge responses"""
    id: int
    organization_id: int
    doc_type: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")
    created_at: datetime
    updated_at: datetime
    
    @staticmethod
    def from_orm(obj):
        """Custom from_orm to handle doc_metadata attribute mapping"""
        return CompanyKnowledgeResponse(
            id=obj.id,
            organization_id=obj.organization_id,
            doc_type=obj.doc_type,
            title=obj.title,
            content=obj.content,
            metadata=obj.doc_metadata if hasattr(obj, 'doc_metadata') else None,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompanyKnowledgeListResponse(BaseModel):
    """Schema for paginated list of company knowledge documents"""
    documents: List[CompanyKnowledgeResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CompanyKnowledgeSearchRequest(BaseModel):
    """Schema for semantic search requests"""
    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    doc_types: Optional[List[DocumentType]] = Field(
        None,
        description="Filter by document types (e.g., ['company_values', 'tech_requirements'])"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to return"
    )
    similarity_threshold: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1)"
    )
    organization_id: Optional[int] = Field(
        None,
        description="Organization ID (auto-detected from auth if not provided)"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Ensure query is meaningful"""
        if len(v.strip()) < 3:
            raise ValueError('Query must be at least 3 characters long')
        return v.strip()


class CompanyKnowledgeSearchResult(BaseModel):
    """Schema for individual search result"""
    id: int
    organization_id: int
    doc_type: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CompanyKnowledgeSearchResponse(BaseModel):
    """Schema for search results response"""
    query: str
    results: List[CompanyKnowledgeSearchResult]
    total_results: int
    search_time_ms: float


class CompanyKnowledgeBulkCreateRequest(BaseModel):
    """Schema for bulk creating multiple documents at once"""
    documents: List[CompanyKnowledgeCreate] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of documents to create (max 50)"
    )
    organization_id: Optional[int] = None


class CompanyKnowledgeBulkCreateResponse(BaseModel):
    """Schema for bulk create response"""
    created: int
    failed: int
    document_ids: List[int]
    errors: List[Dict[str, Any]]


class CompanyKnowledgeStats(BaseModel):
    """Schema for knowledge base statistics"""
    organization_id: int
    total_documents: int
    documents_by_type: Dict[str, int]
    total_content_length: int
    average_content_length: float
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
