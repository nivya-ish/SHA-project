"""create analysis records table

Revision ID: 0001_create_analysis_records
Revises: 
Create Date: 2026-11-20 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_create_analysis_records'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'analysis_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('symptoms_text', sa.Text(), nullable=False),
        sa.Column('duration_text', sa.String(length=255), nullable=True),
        sa.Column('extracted_symptoms', sa.JSON(), nullable=False),
        sa.Column('normalized_symptoms', sa.JSON(), nullable=False),
        sa.Column('mapped_features', sa.JSON(), nullable=False),
        sa.Column('unsupported_symptoms', sa.JSON(), nullable=False),
        sa.Column('predictions', sa.JSON(), nullable=False),
        sa.Column('explanation', sa.JSON(), nullable=True),
        sa.Column('retrieved_sources', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_records_id'), 'analysis_records', ['id'], unique=False)
    op.create_index(op.f('ix_analysis_records_created_at'), 'analysis_records', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_analysis_records_created_at'), table_name='analysis_records')
    op.drop_index(op.f('ix_analysis_records_id'), table_name='analysis_records')
    op.drop_table('analysis_records')
