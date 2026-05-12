"""add_data_hash_to_pipeline_runs

Revision ID: b5d12f4a9e01
Revises: a3f91c2b7e04
Create Date: 2026-05-12 09:17:00.000000

Adds a SHA-256 data_hash column to pipeline_runs to support file deduplication.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b5d12f4a9e01'
down_revision: Union[str, None] = 'a3f91c2b7e04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'pipeline_runs',
        sa.Column('data_hash', sa.String(64), nullable=True),
    )
    op.create_index(
        'ix_pipeline_runs_data_hash',
        'pipeline_runs',
        ['data_hash'],
    )


def downgrade() -> None:
    op.drop_index('ix_pipeline_runs_data_hash', table_name='pipeline_runs')
    op.drop_column('pipeline_runs', 'data_hash')
