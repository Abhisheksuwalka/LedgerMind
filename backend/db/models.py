"""
PostgreSQL models via SQLAlchemy async ORM.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import enum
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://finagent:finagent_pass@postgres:5432/finagent_db",
)

# Render (and Heroku) supply "postgres://" — asyncpg requires "postgresql+asyncpg://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class RunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentStatus(str, enum.Enum):
    idle = "idle"
    running = "running"
    done = "done"
    error = "error"


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# ── Tables ────────────────────────────────────────────────────────────────────

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    triggered_by = Column(String(64), default="schedule")
    status = Column(SAEnum(RunStatus), default=RunStatus.pending)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    data_hash = Column(String(64), nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    # Phase 2: link to the single-tenant business profile
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(512))
    category = Column(String(128))
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    agent_name = Column(String(64))
    action = Column(String(256))
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    llm_provider = Column(String(64), nullable=True)  # was claude_model — now provider-agnostic
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    status = Column(String(16), default="success")
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FinancialReport(Base):
    __tablename__ = "financial_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    pnl_data = Column(JSON, nullable=True)
    forecast_data = Column(JSON, nullable=True)
    anomalies = Column(JSON, nullable=True)
    reconciliation = Column(JSON, nullable=True)
    executive_summary = Column(Text, nullable=True)
    markdown_report = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    transaction_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(String(512))
    reason = Column(Text)
    severity = Column(SAEnum(Severity))
    score = Column(Float)
    recommended_action = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── Phase 2: CashPilot tables ────────────────────────────────────────────────

class BusinessProfile(Base):
    """Single-tenant business profile — one row for the whole app (MVP)."""
    __tablename__ = "business_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), default="My Business")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Accumulated upload stats
    total_uploads = Column(Integer, default=0)
    first_data_date = Column(DateTime(timezone=True), nullable=True)
    latest_data_date = Column(DateTime(timezone=True), nullable=True)

    # Computed health (updated after each upload)
    health_score = Column(Float, default=50.0)
    health_score_history = Column(JSON, default=list)  # [{"date": iso, "score": float}, ...]

    # Rolling revenue / burn summary (EWMA, updated after each upload)
    avg_monthly_revenue = Column(Float, default=0.0)
    avg_monthly_expenses = Column(Float, default=0.0)
    avg_monthly_burn = Column(Float, default=0.0)


class CategoryBaseline(Base):
    """Per-category per-month EWMA baseline — drives anomaly detection in Phase 5+."""
    __tablename__ = "category_baselines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=False)
    category = Column(String(128), nullable=False)
    month_of_year = Column(Integer, nullable=False)  # 1-12
    ewma = Column(Float, nullable=False)              # exponentially weighted moving average spend
    ewmstd = Column(Float, nullable=False)            # EWMA std-dev for Z-score thresholds
    n_observations = Column(Integer, default=0)       # number of monthly samples seen
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    """Persistent alert record — created by Watch Engine (Phase 6) and pipeline nodes."""
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_business_type_created", "business_id", "alert_type", "created_at"),
        Index("ix_alerts_business_dedupe_key", "business_id", "dedupe_key", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=False)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    alert_type = Column(String(64))   # runway_warning | category_spike | margin_trend | digest
    severity = Column(String(16))     # low | medium | high | critical
    title = Column(String(256))
    message = Column(Text)
    dedupe_key = Column(String(64), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ChatMessage(Base):
    """Persisted chat turn — used by the Chat Agent (Phase 4) for memory."""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business_profiles.id"), nullable=False)
    session_id = Column(String(64), nullable=False)
    role = Column(String(16))          # user | assistant | tool
    content = Column(Text)
    tool_calls_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))



# ── Helpers ───────────────────────────────────────────────────────────────────

async def init_db():
    import subprocess
    import sys
    import logging
    logger = logging.getLogger("finagent.db")
    logger.info("Running Alembic migrations...")
    
    # Use the alembic binary in the same directory as the current python executable
    alembic_path = os.path.join(os.path.dirname(sys.executable), "alembic")
    
    try:
        subprocess.run([alembic_path, "upgrade", "head"], check=True, capture_output=True, text=True)
        logger.info("Alembic migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Alembic migration failed: {e.stderr}")
        raise

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
