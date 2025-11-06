"""add_company_knowledge_table

Revision ID: 0601b1021231
Revises: 9b373845d853
Create Date: 2025-11-02 17:58:13.200704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '0601b1021231'
down_revision: Union[str, Sequence[str], None] = '9b373845d853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add company_knowledge table for RAG."""
    # Create company_knowledge table
    op.create_table(
        'company_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(50), nullable=False, comment='Type: company_values, tech_requirements, interview_style, job_description, etc.'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=False, comment='768-dim JobBERT-v3 embedding for similarity search'),
        sa.Column('metadata', JSONB, nullable=True, server_default='{}', comment='Additional metadata like author, source, tags'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for performance
    op.create_index('ix_company_knowledge_organization_id', 'company_knowledge', ['organization_id'])
    op.create_index('ix_company_knowledge_doc_type', 'company_knowledge', ['doc_type'])
    
    # Create vector index for similarity search (using HNSW for speed)
    op.execute('CREATE INDEX ix_company_knowledge_embedding ON company_knowledge USING hnsw (embedding vector_cosine_ops)')


def downgrade() -> None:
    """Downgrade schema - Remove company_knowledge table."""
    op.drop_index('ix_company_knowledge_embedding', table_name='company_knowledge')
    op.drop_index('ix_company_knowledge_doc_type', table_name='company_knowledge')
    op.drop_index('ix_company_knowledge_organization_id', table_name='company_knowledge')
    op.drop_table('company_knowledge')
