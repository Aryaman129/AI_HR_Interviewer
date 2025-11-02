"""add_interview_session_tracking

Revision ID: 9b373845d853
Revises: 013729f283d5
Create Date: 2025-11-02 07:32:00.869668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '9b373845d853'
down_revision: Union[str, Sequence[str], None] = '013729f283d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add interview session tracking fields to screenings table."""
    
    # Add session state tracking
    op.add_column('screenings', sa.Column('session_state', sa.String(50), nullable=True, server_default='in_progress'))
    
    # Add session timing fields
    op.add_column('screenings', sa.Column('paused_at', sa.DateTime(), nullable=True))
    op.add_column('screenings', sa.Column('resumed_at', sa.DateTime(), nullable=True))
    op.add_column('screenings', sa.Column('last_activity_at', sa.DateTime(), nullable=True))
    
    # Add session metadata with scoring details, transcript, key points
    op.add_column('screenings', sa.Column('session_metadata', JSONB, nullable=True))
    # session_metadata structure:
    # {
    #   "pause_count": 0,
    #   "total_paused_seconds": 0,
    #   "time_per_question": [45, 120, 89],  # seconds per question
    #   "recording_url": "https://storage/interview_123.mp4",  # optional
    #   "transcript": [  # conversation transcript
    #     {"speaker": "ai", "text": "Tell me about your Python experience", "timestamp": "00:00:05"},
    #     {"speaker": "candidate", "text": "I have 5 years experience...", "timestamp": "00:00:10"}
    #   ],
    #   "key_points_discussed": [  # extracted key topics
    #     "Python experience - 5 years",
    #     "FastAPI - built 3 production APIs",
    #     "Database - PostgreSQL, MongoDB"
    #   ],
    #   "ai_observations": [  # real-time AI notes
    #     "Candidate showed strong technical depth",
    #     "Communication style: clear and concise",
    #     "Hesitated on system design question"
    #   ]
    # }
    
    # Add detailed scoring breakdown
    op.add_column('screenings', sa.Column('scoring_breakdown', JSONB, nullable=True))
    # scoring_breakdown structure:
    # {
    #   "question_scores": [
    #     {
    #       "question_id": 1,
    #       "score": 8,
    #       "max_score": 10,
    #       "reason": "Demonstrated strong understanding of async/await",
    #       "criteria_met": ["depth", "clarity", "examples"],
    #       "criteria_missed": ["edge_cases"]
    #     }
    #   ],
    #   "category_scores": {
    #     "technical_skills": 85,
    #     "problem_solving": 75,
    #     "communication": 90,
    #     "cultural_fit": 80
    #   },
    #   "scoring_rationale": "Strong technical candidate with excellent communication"
    # }
    
    # Create index for session state queries
    op.create_index('ix_screenings_session_state', 'screenings', ['session_state'])


def downgrade() -> None:
    """Remove interview session tracking fields."""
    
    # Drop index
    op.drop_index('ix_screenings_session_state', table_name='screenings')
    
    # Remove columns
    op.drop_column('screenings', 'scoring_breakdown')
    op.drop_column('screenings', 'session_metadata')
    op.drop_column('screenings', 'last_activity_at')
    op.drop_column('screenings', 'resumed_at')
    op.drop_column('screenings', 'paused_at')
    op.drop_column('screenings', 'session_state')
