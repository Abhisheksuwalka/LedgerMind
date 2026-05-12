"""add_cashpilot_tables

Revision ID: a3f91c2b7e04
Revises: 120b28443fb2
Create Date: 2026-05-12 02:19:00.000000

Phase 2: adds business_profiles, category_baselines, alerts, chat_messages
         and a business_id FK column on transactions.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3f91c2b7e04'
down_revision: Union[str, None] = '120b28443fb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── business_profiles ────────────────────────────────────────────────────
    op.create_table(
        'business_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(256), nullable=True, server_default='My Business'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_uploads', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('first_data_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('latest_data_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=True, server_default='50.0'),
        sa.Column('health_score_history', sa.JSON(), nullable=True),
        sa.Column('avg_monthly_revenue', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('avg_monthly_expenses', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('avg_monthly_burn', sa.Float(), nullable=True, server_default='0.0'),
    )

    # ── category_baselines ───────────────────────────────────────────────────
    op.create_table(
        'category_baselines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('business_profiles.id'), nullable=False),
        sa.Column('category', sa.String(128), nullable=False),
        sa.Column('month_of_year', sa.Integer(), nullable=False),
        sa.Column('ewma', sa.Float(), nullable=False),
        sa.Column('ewmstd', sa.Float(), nullable=False),
        sa.Column('n_observations', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        'ix_category_baselines_business_cat_month',
        'category_baselines',
        ['business_id', 'category', 'month_of_year'],
        unique=True,
    )

    # ── alerts ───────────────────────────────────────────────────────────────
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('business_profiles.id'), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('alert_type', sa.String(64), nullable=True),
        sa.Column('severity', sa.String(16), nullable=True),
        sa.Column('title', sa.String(256), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── chat_messages ────────────────────────────────────────────────────────
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('business_profiles.id'), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=False),
        sa.Column('role', sa.String(16), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('tool_calls_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── Add business_id FK to transactions ───────────────────────────────────
    op.add_column(
        'transactions',
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_transactions_business_id',
        'transactions',
        'business_profiles',
        ['business_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_transactions_business_id', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'business_id')
    op.drop_table('chat_messages')
    op.drop_table('alerts')
    op.drop_index('ix_category_baselines_business_cat_month', table_name='category_baselines')
    op.drop_table('category_baselines')
    op.drop_table('business_profiles')
