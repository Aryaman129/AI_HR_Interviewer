"""add_session_tracking_and_multi_tenant_to_interviews

Revision ID: 1b87ab8285b7
Revises: 0601b1021231
Create Date: 2025-11-08 00:54:46.033755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Import pgvector if available
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

# revision identifiers, used by Alembic.
revision: str = '1b87ab8285b7'
down_revision: Union[str, Sequence[str], None] = '0601b1021231'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add session tracking and multi-tenant support to interviews."""
    # Add multi-tenant fields
    op.add_column('interviews', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.add_column('interviews', sa.Column('client_id', sa.Integer(), nullable=True))
    
    # Add session tracking fields
    op.add_column('interviews', sa.Column('session_state', sa.String(length=50), nullable=True))
    op.add_column('interviews', sa.Column('paused_at', sa.DateTime(), nullable=True))
    op.add_column('interviews', sa.Column('resumed_at', sa.DateTime(), nullable=True))
    op.add_column('interviews', sa.Column('last_activity_at', sa.DateTime(), nullable=True))
    op.add_column('interviews', sa.Column('pause_count', sa.Integer(), nullable=True))
    
    # Create indexes for multi-tenant queries
    op.create_index(op.f('ix_interviews_client_id'), 'interviews', ['client_id'], unique=False)
    op.create_index(op.f('ix_interviews_organization_id'), 'interviews', ['organization_id'], unique=False)
    
    # Create foreign key to organizations
    op.create_foreign_key(None, 'interviews', 'organizations', ['organization_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema - Remove session tracking and multi-tenant support from interviews."""
    # Drop foreign key constraint
    op.drop_constraint(None, 'interviews', type_='foreignkey')
    
    # Drop indexes
    op.drop_index(op.f('ix_interviews_organization_id'), table_name='interviews')
    op.drop_index(op.f('ix_interviews_client_id'), table_name='interviews')
    
    # Drop session tracking columns
    op.drop_column('interviews', 'pause_count')
    op.drop_column('interviews', 'last_activity_at')
    op.drop_column('interviews', 'resumed_at')
    op.drop_column('interviews', 'paused_at')
    op.drop_column('interviews', 'session_state')
    
    # Drop multi-tenant columns
    op.drop_column('interviews', 'client_id')
    op.drop_column('interviews', 'organization_id')
