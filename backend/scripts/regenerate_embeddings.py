#!/usr/bin/env python
"""
Regenerate all embeddings using JobBERT-v3 (768-dim).

This script regenerates embeddings for:
- All candidate resumes and skills
- All job descriptions and skills

Run this after the vector dimension upgrade migration.

Usage:
    python scripts/regenerate_embeddings.py [--batch-size 50] [--dry-run]

Options:
    --batch-size: Number of records to process in each batch (default: 50)
    --dry-run: Show what would be done without making changes
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from tqdm import tqdm

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.embedding_service import get_embedding_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'regenerate_embeddings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class EmbeddingRegenerator:
    """Regenerate embeddings with JobBERT-v3 (768-dim)."""
    
    def __init__(self, batch_size: int = 50, dry_run: bool = False):
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.embedding_service = get_embedding_service()
        
        # Create database session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        self.db: Session = SessionLocal()
        
        # Statistics
        self.stats = {
            'candidates_total': 0,
            'candidates_processed': 0,
            'candidates_errors': 0,
            'jobs_total': 0,
            'jobs_processed': 0,
            'jobs_errors': 0,
            'start_time': None,
            'end_time': None,
        }
    
    def close(self):
        """Close database connection."""
        self.db.close()
    
    def verify_vector_dimensions(self) -> bool:
        """Verify that vector columns are 768-dim."""
        logger.info("Verifying vector column dimensions...")
        
        try:
            # Check candidates table
            result = self.db.execute(text("""
                SELECT 
                    a.attname as column_name,
                    t.typname as type_name,
                    a.atttypmod as type_modifier
                FROM pg_attribute a
                JOIN pg_type t ON a.atttypid = t.oid
                JOIN pg_class c ON a.attrelid = c.oid
                WHERE c.relname = 'candidates'
                AND a.attname IN ('resume_embedding', 'skills_embedding')
                AND NOT a.attisdropped
                ORDER BY a.attname;
            """))
            
            candidates_dims = {row[0]: row[2] for row in result}
            
            # Check jobs table
            result = self.db.execute(text("""
                SELECT 
                    a.attname as column_name,
                    t.typname as type_name,
                    a.atttypmod as type_modifier
                FROM pg_attribute a
                JOIN pg_type t ON a.atttypid = t.oid
                JOIN pg_class c ON a.attrelid = c.oid
                WHERE c.relname = 'jobs'
                AND a.attname IN ('job_description_embedding', 'skills_embedding')
                AND NOT a.attisdropped
                ORDER BY a.attname;
            """))
            
            jobs_dims = {row[0]: row[2] for row in result}
            
            # Log results
            logger.info(f"Candidates vector columns: {candidates_dims}")
            logger.info(f"Jobs vector columns: {jobs_dims}")
            
            # Note: atttypmod for vector(768) is typically 772 (768 + 4 for overhead)
            # We just check that it's not 388 (384 + 4)
            
            all_correct = True
            for col, dim in {**candidates_dims, **jobs_dims}.items():
                if dim == 388:  # Old 384-dim
                    logger.error(f"Column {col} still has 384 dimensions!")
                    all_correct = False
            
            if all_correct:
                logger.info("✓ All vector columns appear to be upgraded to 768 dimensions")
            
            return all_correct
            
        except Exception as e:
            logger.error(f"Error verifying dimensions: {e}")
            return False
    
    def get_candidates_to_process(self) -> List[Candidate]:
        """Get all candidates that need embedding regeneration."""
        logger.info("Fetching candidates...")
        
        # Get all candidates (both with NULL embeddings and existing ones)
        candidates = self.db.query(Candidate).all()
        
        self.stats['candidates_total'] = len(candidates)
        logger.info(f"Found {len(candidates)} candidates to process")
        
        return candidates
    
    def get_jobs_to_process(self) -> List[Job]:
        """Get all jobs that need embedding regeneration."""
        logger.info("Fetching jobs...")
        
        # Get all jobs (both with NULL embeddings and existing ones)
        jobs = self.db.query(Job).all()
        
        self.stats['jobs_total'] = len(jobs)
        logger.info(f"Found {len(jobs)} jobs to process")
        
        return jobs
    
    def regenerate_candidate_embeddings(self, candidates: List[Candidate]) -> None:
        """Regenerate embeddings for candidates."""
        logger.info(f"\n{'='*60}")
        logger.info(f"REGENERATING CANDIDATE EMBEDDINGS")
        logger.info(f"{'='*60}")
        
        if self.dry_run:
            logger.info("DRY RUN - No changes will be made")
            return
        
        # Process in batches
        for i in tqdm(range(0, len(candidates), self.batch_size), desc="Processing candidates"):
            batch = candidates[i:i + self.batch_size]
            
            for candidate in batch:
                try:
                    # Build resume text from candidate data
                    resume_text = self._build_resume_text_from_candidate(candidate)
                    
                    # Get skills list (handle both dict and list formats)
                    skills = []
                    if candidate.skills:
                        if isinstance(candidate.skills, dict):
                            # Flatten all skill categories
                            for skill_list in candidate.skills.values():
                                if isinstance(skill_list, list):
                                    skills.extend(skill_list)
                        elif isinstance(candidate.skills, list):
                            skills = candidate.skills
                    
                    # Get experience
                    experience = candidate.work_experience if candidate.work_experience else []
                    
                    # Only generate embeddings if we have data
                    if resume_text or skills:
                        # Generate resume embedding with context
                        resume_embedding = self.embedding_service.generate_resume_embedding(
                            resume_text=resume_text,
                            include_skills=skills if skills else None,
                            include_experience=experience if experience else None
                        )
                        candidate.resume_embedding = resume_embedding
                        
                        # Generate skills embedding
                        if skills:
                            skills_embedding = self.embedding_service.generate_skills_embedding(skills)
                            candidate.skills_embedding = skills_embedding
                        
                        self.stats['candidates_processed'] += 1
                        logger.debug(f"Processed candidate {candidate.id} ({candidate.full_name})")
                    else:
                        logger.warning(f"Skipping candidate {candidate.id} - no data to embed")
                    
                except Exception as e:
                    logger.error(f"Error processing candidate {candidate.id}: {e}")
                    self.stats['candidates_errors'] += 1
            
            # Commit batch
            try:
                self.db.commit()
                logger.debug(f"Committed batch of {len(batch)} candidates")
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                self.db.rollback()
    
    def regenerate_job_embeddings(self, jobs: List[Job]) -> None:
        """Regenerate embeddings for jobs."""
        logger.info(f"\n{'='*60}")
        logger.info(f"REGENERATING JOB EMBEDDINGS")
        logger.info(f"{'='*60}")
        
        if self.dry_run:
            logger.info("DRY RUN - No changes will be made")
            return
        
        # Process in batches
        for i in tqdm(range(0, len(jobs), self.batch_size), desc="Processing jobs"):
            batch = jobs[i:i + self.batch_size]
            
            for job in batch:
                try:
                    # Only process if we have a description
                    if job.description:
                        # Generate job description embedding
                        job_description_embedding = self.embedding_service.generate_job_embedding(
                            job_description=job.description,
                            required_skills=job.required_skills,
                            job_title=job.title
                        )
                        job.job_description_embedding = job_description_embedding
                        
                        # Generate skills embedding
                        if job.required_skills:
                            skills_embedding = self.embedding_service.generate_skills_embedding(
                                job.required_skills
                            )
                            job.skills_embedding = skills_embedding
                        
                        self.stats['jobs_processed'] += 1
                        logger.debug(f"Processed job {job.id} ({job.title})")
                    else:
                        logger.warning(f"Skipping job {job.id} - no description")
                    
                except Exception as e:
                    logger.error(f"Error processing job {job.id}: {e}")
                    self.stats['jobs_errors'] += 1
            
            # Commit batch
            try:
                self.db.commit()
                logger.debug(f"Committed batch of {len(batch)} jobs")
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                self.db.rollback()
    
    def _build_resume_text_from_candidate(self, candidate: Candidate) -> str:
        """Build resume text from candidate model fields."""
        parts = []
        
        # Add name
        if candidate.full_name:
            parts.append(f"Name: {candidate.full_name}")
        
        # Add email
        if candidate.email:
            parts.append(f"Email: {candidate.email}")
        
        # Add current role and company
        if candidate.current_role:
            parts.append(f"Current Role: {candidate.current_role}")
        if candidate.current_company:
            parts.append(f"Current Company: {candidate.current_company}")
        
        # Add location
        if candidate.location:
            parts.append(f"Location: {candidate.location}")
        
        # Add total experience
        if candidate.total_experience_years:
            parts.append(f"Total Experience: {candidate.total_experience_years} years")
        
        # Add skills
        if candidate.skills:
            skill_list = []
            if isinstance(candidate.skills, dict):
                # Flatten all skill categories
                for category, skills in candidate.skills.items():
                    if isinstance(skills, list):
                        skill_list.extend(skills)
            elif isinstance(candidate.skills, list):
                skill_list = candidate.skills
            
            if skill_list:
                parts.append(f"Skills: {', '.join(skill_list)}")
        
        # Add work experience
        if candidate.work_experience and isinstance(candidate.work_experience, list):
            parts.append("\nWork Experience:")
            for exp in candidate.work_experience:
                if isinstance(exp, dict):
                    exp_parts = []
                    if exp.get('role'):
                        exp_parts.append(exp['role'])
                    if exp.get('company'):
                        exp_parts.append(f"at {exp['company']}")
                    if exp.get('dates'):
                        exp_parts.append(f"({exp['dates']})")
                    if exp_parts:
                        parts.append("  - " + " ".join(exp_parts))
        
        # Add education
        if candidate.education and isinstance(candidate.education, list):
            parts.append("\nEducation:")
            for edu in candidate.education:
                if isinstance(edu, dict):
                    edu_parts = []
                    if edu.get('degree'):
                        edu_parts.append(edu['degree'])
                    if edu.get('university'):
                        edu_parts.append(f"from {edu['university']}")
                    if edu.get('year'):
                        edu_parts.append(f"({edu['year']})")
                    if edu_parts:
                        parts.append("  - " + " ".join(edu_parts))
        
        # Add certifications
        if candidate.certifications and isinstance(candidate.certifications, list):
            parts.append("\nCertifications:")
            for cert in candidate.certifications:
                if isinstance(cert, dict):
                    cert_name = cert.get('name', '')
                    cert_issued = cert.get('issued', '')
                    if cert_name:
                        parts.append(f"  - {cert_name}" + (f" ({cert_issued})" if cert_issued else ""))
                elif isinstance(cert, str):
                    parts.append(f"  - {cert}")
        
        # Add languages
        if candidate.languages and isinstance(candidate.languages, list):
            parts.append(f"\nLanguages: {', '.join(candidate.languages)}")
        
        # Add resume text if available
        if candidate.resume_text:
            parts.append(f"\nResume Text:\n{candidate.resume_text}")
        
        return "\n".join(parts)
    
    def print_statistics(self) -> None:
        """Print final statistics."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"REGENERATION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        logger.info(f"\nCandidates:")
        logger.info(f"  Total: {self.stats['candidates_total']}")
        logger.info(f"  Processed: {self.stats['candidates_processed']}")
        logger.info(f"  Errors: {self.stats['candidates_errors']}")
        logger.info(f"\nJobs:")
        logger.info(f"  Total: {self.stats['jobs_total']}")
        logger.info(f"  Processed: {self.stats['jobs_processed']}")
        logger.info(f"  Errors: {self.stats['jobs_errors']}")
        logger.info(f"\nTotal Records:")
        logger.info(f"  Processed: {self.stats['candidates_processed'] + self.stats['jobs_processed']}")
        logger.info(f"  Errors: {self.stats['candidates_errors'] + self.stats['jobs_errors']}")
        logger.info(f"  Success Rate: {((self.stats['candidates_processed'] + self.stats['jobs_processed']) / (self.stats['candidates_total'] + self.stats['jobs_total']) * 100):.1f}%")
        
        if self.dry_run:
            logger.info(f"\n⚠️  This was a DRY RUN - no changes were made")
        else:
            logger.info(f"\n✅ Embeddings regenerated successfully!")
    
    def run(self) -> None:
        """Run the regeneration process."""
        try:
            self.stats['start_time'] = datetime.now()
            
            logger.info("="*60)
            logger.info("EMBEDDING REGENERATION SCRIPT")
            logger.info(f"JobBERT-v3 (768 dimensions)")
            logger.info(f"Batch size: {self.batch_size}")
            logger.info(f"Dry run: {self.dry_run}")
            logger.info("="*60)
            
            # Verify vector dimensions
            if not self.verify_vector_dimensions():
                logger.error("Vector dimensions not correct. Run migration first!")
                return
            
            # Get records to process
            candidates = self.get_candidates_to_process()
            jobs = self.get_jobs_to_process()
            
            if not candidates and not jobs:
                logger.info("No records to process. Exiting.")
                return
            
            # Regenerate embeddings
            if candidates:
                self.regenerate_candidate_embeddings(candidates)
            
            if jobs:
                self.regenerate_job_embeddings(jobs)
            
            self.stats['end_time'] = datetime.now()
            
            # Print statistics
            self.print_statistics()
            
        except KeyboardInterrupt:
            logger.warning("\n\n⚠️  Process interrupted by user")
            self.db.rollback()
        except Exception as e:
            logger.error(f"\n\n❌ Fatal error: {e}", exc_info=True)
            self.db.rollback()
        finally:
            self.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Regenerate embeddings with JobBERT-v3 (768-dim)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Regenerate all embeddings (default batch size)
  python scripts/regenerate_embeddings.py
  
  # Use larger batch size for faster processing
  python scripts/regenerate_embeddings.py --batch-size 100
  
  # Dry run to see what would be done
  python scripts/regenerate_embeddings.py --dry-run
        """
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of records to process in each batch (default: 50)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    # Run regeneration
    regenerator = EmbeddingRegenerator(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    regenerator.run()


if __name__ == '__main__':
    main()
