"""add_alert_dedupe_indexes

Revision ID: c7e91ab44a11
Revises: b5d12f4a9e01
Create Date: 2026-05-13 12:05:00.000000

Adds alert dedupe key and supporting indexes for recurring watch jobs.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7e91ab44a11"
down_revision: Union[str, None] = "b5d12f4a9e01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("dedupe_key", sa.String(length=64), nullable=True))
    op.create_index(
        "ix_alerts_business_type_created",
        "alerts",
        ["business_id", "alert_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_alerts_business_dedupe_key",
        "alerts",
        ["business_id", "dedupe_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_alerts_business_dedupe_key", table_name="alerts")
    op.drop_index("ix_alerts_business_type_created", table_name="alerts")
    op.drop_column("alerts", "dedupe_key")
