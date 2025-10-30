"""
Resume API Endpoints
Handles resume upload, parsing, and candidate creation.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict
import os
import tempfile
import logging

from app.db.database import get_db
from app.models.candidate import Candidate, CandidateStatus
from app.models.resume import Resume
from app.services.resume_parser import get_resume_parser
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("/parse", response_model=Dict)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a resume file.
    
    - Extracts text from PDF/DOCX
    - Parses contact info, skills, education, experience
    - Generates 384-dim embeddings for semantic search
    - Creates Candidate and Resume records in database
    
    Returns:
        Candidate ID, parsed data, and confidence score
    """
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.pdf', '.docx', '.doc']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Use PDF or DOCX."
        )
    
    # Save uploaded file temporarily
    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Uploaded file saved: {tmp_file_path}")
        
        # Parse resume
        parser = get_resume_parser()
        parsed_data = parser.parse(tmp_file_path)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error parsing resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")
    finally:
        # Clean up temp file
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
    
    # Check if candidate already exists (by email)
    email = parsed_data.get('email')
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Could not extract email from resume. Please ensure resume contains valid email address."
        )
    
    existing_candidate = db.query(Candidate).filter(Candidate.email == email).first()
    
    if existing_candidate:
        # Update existing candidate
        candidate = existing_candidate
        candidate.phone = parsed_data.get('phone') or candidate.phone
        candidate.full_name = parsed_data.get('full_name') or candidate.full_name
        candidate.location = parsed_data.get('location') or candidate.location
        candidate.skills = parsed_data.get('skills')
        candidate.education = parsed_data.get('education')
        candidate.work_experience = parsed_data.get('work_experience')
        candidate.total_experience_years = parsed_data.get('total_experience_years')
        candidate.resume_embedding = parsed_data.get('resume_embedding')
        candidate.skills_embedding = parsed_data.get('skills_embedding')
        
        logger.info(f"Updated existing candidate: {email}")
    else:
        # Create new candidate
        candidate = Candidate(
            email=email,
            phone=parsed_data.get('phone'),
            full_name=parsed_data.get('full_name'),
            location=parsed_data.get('location'),
            skills=parsed_data.get('skills'),
            education=parsed_data.get('education'),
            work_experience=parsed_data.get('work_experience'),
            total_experience_years=parsed_data.get('total_experience_years'),
            resume_embedding=parsed_data.get('resume_embedding'),
            skills_embedding=parsed_data.get('skills_embedding'),
            status=CandidateStatus.NEW
        )
        db.add(candidate)
        logger.info(f"Created new candidate: {email}")
    
    # Commit candidate first to get ID
    db.commit()
    db.refresh(candidate)
    
    # Create Resume record
    # Remove embeddings from parsed_data before storing as JSONB (embeddings are already in candidate table)
    parsed_data_for_storage = {k: v for k, v in parsed_data.items() 
                                if k not in ['resume_embedding', 'skills_embedding']}
    
    resume = Resume(
        candidate_id=candidate.id,
        filename=file.filename,
        file_type=file_ext.replace('.', ''),
        raw_text=parsed_data.get('raw_text'),
        parsed_data=parsed_data_for_storage,  # Store parsed data without embeddings
        processing_status='completed',
        processed_at=datetime.utcnow()
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    logger.info(f"Created resume record ID: {resume.id} for candidate ID: {candidate.id}")
    
    # Build response
    return {
        "success": True,
        "candidate_id": candidate.id,
        "resume_id": resume.id,
        "email": candidate.email,
        "full_name": candidate.full_name,
        "parsed_data": {
            "skills": parsed_data.get('skills'),
            "education": parsed_data.get('education'),
            "work_experience": parsed_data.get('work_experience'),
            "total_experience_years": parsed_data.get('total_experience_years')
        },
        "embeddings_generated": True,
        "message": "Resume parsed and stored successfully"
    }


@router.get("/search", response_model=Dict)
async def semantic_search(
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Search for candidates using semantic similarity.
    
    - Generates embedding for search query
    - Finds candidates with similar resume embeddings using pgvector
    - Returns top N matches sorted by similarity
    
    Args:
        query: Search text (e.g., "Python developer with 5 years experience")
        limit: Maximum number of results (default 5)
    
    Returns:
        List of candidates with similarity scores
    """
    
    if not query or len(query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
    
    # Generate embedding for query
    parser = get_resume_parser()
    query_embedding, _ = parser.generate_embeddings(query)
    query_embedding_list = query_embedding.tolist()
    
    # pgvector cosine similarity search
    # Using raw SQL for pgvector operators
    from sqlalchemy import text
    
    sql = text("""
        SELECT 
            id,
            email,
            full_name,
            location,
            skills,
            total_experience_years,
            1 - (resume_embedding <=> :query_embedding) AS similarity
        FROM candidates
        WHERE resume_embedding IS NOT NULL
        ORDER BY resume_embedding <=> :query_embedding
        LIMIT :limit
    """)
    
    result = db.execute(sql, {
        'query_embedding': str(query_embedding_list),
        'limit': limit
    })
    
    candidates = []
    for row in result:
        candidates.append({
            'candidate_id': row.id,
            'email': row.email,
            'full_name': row.full_name,
            'location': row.location,
            'skills': row.skills,
            'total_experience_years': row.total_experience_years,
            'similarity_score': float(row.similarity)
        })
    
    return {
        "success": True,
        "query": query,
        "results_count": len(candidates),
        "candidates": candidates
    }
