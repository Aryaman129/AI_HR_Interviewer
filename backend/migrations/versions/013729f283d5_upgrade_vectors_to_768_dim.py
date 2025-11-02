"""upgrade_vectors_to_768_dim

Upgrade vector embeddings from 384-dim (MiniLM) to 768-dim (JobBERT-v3).

This migration:
1. Drops existing vector indexes
2. Alters vector columns from 384 to 768 dimensions
3. Creates new ivfflat indexes optimized for 768-dim vectors
4. Note: Existing embeddings will need to be regenerated after migration

Revision ID: 013729f283d5
Revises: 6874fc7b8a2a
Create Date: 2025-11-02 06:22:48.794674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '013729f283d5'
down_revision: Union[str, Sequence[str], None] = '6874fc7b8a2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade vector dimensions from 384 to 768 for JobBERT-v3.
    
    WARNING: This will null out all existing embeddings. 
    Run regenerate_embeddings.py script after migration.
    """
    
    # Step 1: Drop existing vector indexes
    print("Dropping old vector indexes...")
    
    # Drop candidates indexes
    op.execute("DROP INDEX IF EXISTS idx_candidates_resume_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_candidates_skills_embedding;")
    
    # Drop jobs indexes
    op.execute("DROP INDEX IF EXISTS idx_jobs_job_description_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_skills_embedding;")
    
    print("✓ Old indexes dropped")
    
    # Step 2: Set existing embeddings to NULL and change column types
    print("Updating vector column dimensions...")
    
    # Candidates table - null out old embeddings and change dimensions
    op.execute("UPDATE candidates SET resume_embedding = NULL, skills_embedding = NULL;")
    op.execute("ALTER TABLE candidates ALTER COLUMN resume_embedding TYPE vector(768);")
    op.execute("ALTER TABLE candidates ALTER COLUMN skills_embedding TYPE vector(768);")
    
    # Jobs table - null out old embeddings and change dimensions
    op.execute("UPDATE jobs SET job_description_embedding = NULL, skills_embedding = NULL;")
    op.execute("ALTER TABLE jobs ALTER COLUMN job_description_embedding TYPE vector(768);")
    op.execute("ALTER TABLE jobs ALTER COLUMN skills_embedding TYPE vector(768);")
    
    print("✓ Vector columns upgraded to 768 dimensions")
    
    # Step 3: Create new ivfflat indexes for 768-dim vectors
    print("Creating new vector indexes...")
    
    # Create indexes for candidates
    # Using lists=100 for ~10,000 vectors, adjust based on your data size
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_resume_embedding 
        ON candidates USING ivfflat (resume_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_skills_embedding 
        ON candidates USING ivfflat (skills_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    # Create indexes for jobs
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_job_description_embedding 
        ON jobs USING ivfflat (job_description_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_skills_embedding 
        ON jobs USING ivfflat (skills_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    print("✓ New vector indexes created")
    print("\n⚠️  IMPORTANT: Run 'python scripts/regenerate_embeddings.py' to regenerate all embeddings!")


def downgrade() -> None:
    """
    Downgrade vector dimensions from 768 back to 384.
    
    WARNING: This will null out all existing embeddings.
    """
    
    # Drop 768-dim indexes
    op.execute("DROP INDEX IF EXISTS idx_candidates_resume_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_candidates_skills_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_job_description_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_skills_embedding;")
    
    # Null embeddings and change back to 384 dimensions
    op.execute("UPDATE candidates SET resume_embedding = NULL, skills_embedding = NULL;")
    op.execute("ALTER TABLE candidates ALTER COLUMN resume_embedding TYPE vector(384);")
    op.execute("ALTER TABLE candidates ALTER COLUMN skills_embedding TYPE vector(384);")
    
    op.execute("UPDATE jobs SET job_description_embedding = NULL, skills_embedding = NULL;")
    op.execute("ALTER TABLE jobs ALTER COLUMN job_description_embedding TYPE vector(384);")
    op.execute("ALTER TABLE jobs ALTER COLUMN skills_embedding TYPE vector(384);")
    
    # Recreate 384-dim indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_resume_embedding 
        ON candidates USING ivfflat (resume_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_skills_embedding 
        ON candidates USING ivfflat (skills_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_job_description_embedding 
        ON jobs USING ivfflat (job_description_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_skills_embedding 
        ON jobs USING ivfflat (skills_embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)
    
    print("⚠️  Downgraded to 384 dimensions. Regenerate embeddings with old model.")
