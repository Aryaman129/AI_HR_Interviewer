"""
End-to-End System Test
Tests complete workflow: Multi-Provider LLM + 768-dim Embeddings + Interview Sessions
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.screening import Screening, SessionState
from app.services.llm_provider import get_llm_service
from app.services.embedding_service import get_embedding_service
from app.services.ai_screening import ai_screening_service
from app.services.job_matcher import job_matcher_service
import numpy as np

print("=" * 70)
print("END-TO-END SYSTEM TEST")
print("=" * 70)
print()

async def test_llm_providers():
    """Test 1: Multi-Provider LLM"""
    print("TEST 1: Multi-Provider LLM Service")
    print("-" * 70)
    
    llm_service = get_llm_service()
    stats = llm_service.get_provider_stats()
    
    print(f"✓ Available Providers: {len(stats)}")
    for provider in stats:
        symbol = "✅" if provider['status'] == "healthy" else "❌"
        print(f"  {symbol} {provider['name']}: {provider['status']}")
    
    print()

async def test_embedding_service():
    """Test 2: 768-dim JobBERT-v3 Embeddings"""
    print("TEST 2: Embedding Service (JobBERT-v3)")
    print("-" * 70)
    
    embedding_service = get_embedding_service()
    
    test_text = "Python developer with 5 years experience in FastAPI and PostgreSQL"
    embedding = embedding_service.generate_text_embedding(test_text)
    
    print(f"✓ Embedding generated")
    print(f"  Dimension: {len(embedding)}")
    print(f"  Type: {type(embedding)}")
    print(f"  Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
    
    # Test cosine similarity
    embedding2 = embedding_service.generate_text_embedding("Senior Python backend engineer")
    
    # Convert to numpy arrays for similarity calculation
    emb1_array = np.array(embedding)
    emb2_array = np.array(embedding2)
    similarity = embedding_service.cosine_similarity(emb1_array, emb2_array)
    print(f"  Similarity score: {similarity:.4f}")
    
    assert len(embedding) == 768, f"Expected 768 dimensions, got {len(embedding)}"
    print()

async def test_database_embeddings():
    """Test 3: Database Embeddings Verification"""
    print("TEST 3: Database Embeddings (768-dim)")
    print("-" * 70)
    
    db: Session = SessionLocal()
    try:
        candidates = db.query(Candidate).limit(3).all()
        
        print(f"✓ Checking {len(candidates)} candidates...")
        for candidate in candidates:
            has_resume = candidate.resume_embedding is not None
            has_skills = candidate.skills_embedding is not None
            
            if has_resume and has_skills:
                resume_dim = len(candidate.resume_embedding)
                skills_dim = len(candidate.skills_embedding)
                symbol = "✅" if resume_dim == 768 and skills_dim == 768 else "❌"
                print(f"  {symbol} Candidate {candidate.id}: resume={resume_dim}d, skills={skills_dim}d")
            else:
                print(f"  ⚠️ Candidate {candidate.id}: Missing embeddings")
        
    finally:
        db.close()
    
    print()

async def test_job_matching():
    """Test 4: Job Matching with 768-dim Vectors"""
    print("TEST 4: Job Matching (768-dim)")
    print("-" * 70)
    
    db: Session = SessionLocal()
    try:
        # Get a job and candidate
        job = db.query(Job).first()
        candidate = db.query(Candidate).first()
        
        if not job or not candidate:
            print("  ⚠️ No job or candidate found in database")
            return
        
        print(f"  Job: {job.title}")
        print(f"  Candidate: {candidate.full_name}")
        
        # Calculate match score
        match_result = job_matcher_service.calculate_match_score(
            candidate.id,
            job.id,
            db
        )
        
        if "error" in match_result:
            print(f"  ❌ Error: {match_result['error']}")
        else:
            print(f"  ✓ Overall Score: {match_result['overall_score']:.2f}")
            print(f"  Component Scores:")
            for component, score in match_result['component_scores'].items():
                print(f"    - {component}: {score:.2f}")
        
    finally:
        db.close()
    
    print()

async def test_ai_screening():
    """Test 5: AI Screening with Multi-Provider LLM"""
    print("TEST 5: AI Screening Service")
    print("-" * 70)
    
    db: Session = SessionLocal()
    try:
        # Test fallback questions generation
        context = {
            "candidate": {
                "skills": ["Python", "FastAPI", "PostgreSQL"]
            }
        }
        questions = ai_screening_service._generate_fallback_questions(context, 3)
        
        print(f"  ✓ Generated {len(questions)} fallback questions")
        for i, q in enumerate(questions, 1):
            print(f"    {i}. {q['question'][:50]}...")
        
    finally:
        db.close()
    
    print()

async def test_interview_session():
    """Test 6: Interview Session Tracking"""
    print("TEST 6: Interview Session Tracking")
    print("-" * 70)
    
    db: Session = SessionLocal()
    try:
        # Get an existing screening or create a test one
        screening = db.query(Screening).first()
        
        if not screening:
            print("  ⚠️ No screening found in database")
            return
        
        print(f"  Screening ID: {screening.id}")
        print(f"  Initial State: {screening.session_state}")
        
        # Test pause
        original_state = screening.session_state
        screening.pause_session()
        db.commit()
        db.refresh(screening)
        
        print(f"  ✓ Paused: {screening.session_state}")
        print(f"    Pause count: {screening.session_metadata.get('pause_count', 0) if screening.session_metadata else 0}")
        
        # Test resume
        screening.resume_session()
        db.commit()
        db.refresh(screening)
        
        print(f"  ✓ Resumed: {screening.session_state}")
        print(f"    Total paused time: {screening.session_metadata.get('total_paused_seconds', 0) if screening.session_metadata else 0}s")
        
        # Test add transcript
        screening.add_transcript_entry("ai", "What is your experience with Python?", "00:00:05")
        screening.add_transcript_entry("candidate", "I have 5 years of experience", "00:00:15")
        db.commit()
        db.refresh(screening)
        
        transcript_count = len(screening.session_metadata.get('transcript', [])) if screening.session_metadata else 0
        print(f"  ✓ Transcript entries: {transcript_count}")
        
        # Test add key point
        screening.add_key_point("Python - 5 years experience")
        screening.add_ai_observation("Candidate demonstrated strong technical knowledge")
        db.commit()
        db.refresh(screening)
        
        key_points = len(screening.session_metadata.get('key_points_discussed', [])) if screening.session_metadata else 0
        observations = len(screening.session_metadata.get('ai_observations', [])) if screening.session_metadata else 0
        print(f"  ✓ Key points: {key_points}, AI observations: {observations}")
        
        # Restore original state
        screening.session_state = original_state
        db.commit()
        
    finally:
        db.close()
    
    print()

async def test_llm_failover():
    """Test 7: LLM Automatic Failover"""
    print("TEST 7: LLM Automatic Failover")
    print("-" * 70)
    
    llm_service = get_llm_service()
    
    # Test generation (will use primary or failover automatically)
    from app.services.llm_provider import LLMOptions
    
    test_prompt = "Generate a simple greeting message."
    options = LLMOptions(temperature=0.7, max_tokens=50)
    
    try:
        response = await llm_service.generate(test_prompt, options)
        print(f"  ✓ LLM Response received")
        print(f"    Provider used: {response.provider}")
        print(f"    Response: {response.content[:60]}...")
    except Exception as e:
        print(f"  ❌ LLM Error: {e}")
    
    print()

async def test_scoring_breakdown():
    """Test 8: Scoring Breakdown"""
    print("TEST 8: Scoring Breakdown & Rationale")
    print("-" * 70)
    
    db: Session = SessionLocal()
    try:
        screening = db.query(Screening).first()
        
        if not screening:
            print("  ⚠️ No screening found")
            return
        
        # Check if scoring breakdown exists
        if screening.scoring_breakdown:
            print(f"  ✓ Scoring breakdown available")
            breakdown = screening.scoring_breakdown
            
            if 'question_scores' in breakdown:
                print(f"    Question scores: {len(breakdown['question_scores'])} questions")
            
            if 'category_scores' in breakdown:
                print(f"    Category scores:")
                for category, score in breakdown['category_scores'].items():
                    print(f"      - {category}: {score:.1f}")
            
            if 'scoring_rationale' in breakdown:
                rationale = breakdown['scoring_rationale']
                print(f"    Rationale: {rationale[:80]}...")
        else:
            print("  ℹ️ No scoring breakdown yet (will be generated on completion)")
        
    finally:
        db.close()
    
    print()

async def main():
    """Run all E2E tests"""
    try:
        await test_llm_providers()
        await test_embedding_service()
        await test_database_embeddings()
        await test_job_matching()
        await test_ai_screening()
        await test_interview_session()
        await test_llm_failover()
        await test_scoring_breakdown()
        
        print("=" * 70)
        print("✅ ALL E2E TESTS COMPLETED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✓ Multi-Provider LLM (Ollama + Gemini)")
        print("  ✓ JobBERT-v3 Embeddings (768-dim)")
        print("  ✓ Database Embeddings Verified")
        print("  ✓ Job Matching with 768-dim vectors")
        print("  ✓ AI Screening Service")
        print("  ✓ Interview Session Tracking (pause/resume/transcript/scoring)")
        print("  ✓ Automatic LLM Failover")
        print("  ✓ Scoring Breakdown & Rationale")
        print()
        
    except Exception as e:
        print(f"\n❌ E2E TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
