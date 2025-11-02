"""add_organizations_and_multi_tenancy

Revision ID: 6874fc7b8a2a
Revises: 8a1410419c92
Create Date: 2025-11-02 05:56:12.445346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '6874fc7b8a2a'
down_revision: Union[str, Sequence[str], None] = '8a1410419c92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add multi-tenancy support."""
    
    # Step 1: Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('company_size', sa.String(length=50), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('headquarters_location', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=50), server_default='UTC'),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('plan', sa.String(length=50), server_default='free'),
        sa.Column('max_users', sa.Integer(), server_default='3'),
        sa.Column('max_jobs', sa.Integer(), server_default='5'),
        sa.Column('max_candidates', sa.Integer(), server_default='100'),
        sa.Column('current_users_count', sa.Integer(), server_default='0'),
        sa.Column('current_jobs_count', sa.Integer(), server_default='0'),
        sa.Column('current_candidates_count', sa.Integer(), server_default='0'),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('subscription_status', sa.String(length=50), nullable=True),
        sa.Column('subscription_started_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)
    op.create_index(op.f('ix_organizations_is_active'), 'organizations', ['is_active'], unique=False)
    
    # Create company_knowledge table
    op.create_table(
        'company_knowledge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=False),  # JobBERT-v3 uses 768-dim (BERT-base)
        sa.Column('doc_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for company_knowledge
    op.create_index('idx_company_knowledge_id', 'company_knowledge', ['id'])
    op.create_index('idx_company_knowledge_organization_id', 'company_knowledge', ['organization_id'])
    op.create_index('idx_company_knowledge_document_type', 'company_knowledge', ['document_type'])
    op.create_index('idx_company_knowledge_is_active', 'company_knowledge', ['is_active'])
    
    # Create vector index for semantic search (if not exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_company_knowledge_embedding 
        ON company_knowledge USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100)
    """)
    
    # Step 3: Add organization_id to existing tables
    
    # Add to users table
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    op.create_foreign_key('fk_users_organization_id', 'users', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    
    # Add to jobs table
    op.add_column('jobs', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_jobs_organization_id'), 'jobs', ['organization_id'], unique=False)
    op.create_foreign_key('fk_jobs_organization_id', 'jobs', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    
    # Add to candidates table
    op.add_column('candidates', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_candidates_organization_id'), 'candidates', ['organization_id'], unique=False)
    op.create_foreign_key('fk_candidates_organization_id', 'candidates', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema - Remove multi-tenancy support."""
    
    # Remove organization_id from existing tables
    op.drop_constraint('fk_candidates_organization_id', 'candidates', type_='foreignkey')
    op.drop_index(op.f('ix_candidates_organization_id'), table_name='candidates')
    op.drop_column('candidates', 'organization_id')
    
    op.drop_constraint('fk_jobs_organization_id', 'jobs', type_='foreignkey')
    op.drop_index(op.f('ix_jobs_organization_id'), table_name='jobs')
    op.drop_column('jobs', 'organization_id')
    
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_column('users', 'organization_id')
    
    # Drop company_knowledge table
    op.execute("DROP INDEX IF EXISTS idx_company_knowledge_embedding")
    op.drop_index(op.f('ix_company_knowledge_is_active'), table_name='company_knowledge')
    op.drop_index(op.f('ix_company_knowledge_document_type'), table_name='company_knowledge')
    op.drop_index(op.f('ix_company_knowledge_organization_id'), table_name='company_knowledge')
    op.drop_table('company_knowledge')
    
    # Drop organizations table
    op.drop_index(op.f('ix_organizations_is_active'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
    
    # Drop enum
    sa.Enum(name='documenttype').drop(op.get_bind(), checkfirst=True)
