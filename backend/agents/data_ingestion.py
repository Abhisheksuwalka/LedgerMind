"""
Agent 2 — Data Ingestion Agent
Parses CSV / JSON uploads, normalises transactions, writes to PostgreSQL.
"""

import io
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Transaction

logger = logging.getLogger("agent.ingestion")

REQUIRED_COLUMNS = {"date", "description", "amount"}
CATEGORY_MAP = {
    "salary": "revenue",
    "invoice": "revenue",
    "payment": "expense",
    "rent": "expense",
    "utilities": "expense",
    "software": "expense",
    "travel": "expense",
    "marketing": "expense",
    "refund": "revenue",
}


def _infer_category(description: str) -> str:
    desc_lower = description.lower()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in desc_lower:
            return cat
    return "other"


STRIPE_COLUMNS = {"id", "description", "created (utc)", "amount", "currency", "status", "fee", "net"}

def _is_stripe_export(df: pd.DataFrame) -> bool:
    cols = {c.lower() for c in df.columns}
    return len(STRIPE_COLUMNS & cols) >= 5

def _normalize_stripe(df: pd.DataFrame) -> pd.DataFrame:
    """Map Stripe columns to internal schema."""
    rename = {
        "created (utc)": "date",
        "description": "description",
        "net": "amount",  # use net (after fees)
        "currency": "currency",
    }
    df = df.rename(columns={c: rename[c.lower()] for c in df.columns if c.lower() in rename})
    df = df[["date", "description", "amount", "currency"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    # Stripe amounts are in dollars (not cents for CSV export)
    df["category"] = df["description"].apply(_infer_category)
    # Only include successful charges
    return df[df["amount"] != 0]


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROW_COUNT = 50_000

def validate_file(content: bytes, file_type: str):
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large: {len(content)//1024}KB > 10MB limit")
    if file_type not in ("csv", "json"):
        raise ValueError(f"Unsupported file type: {file_type}. Use csv or json.")

def validate_dataframe(df: pd.DataFrame):
    if len(df) > MAX_ROW_COUNT:
        raise ValueError(f"Too many rows: {len(df)} > {MAX_ROW_COUNT} limit")
    if len(df) < 4:
        raise ValueError(f"Too few transactions: need at least 4 rows for analysis")
    if df["amount"].abs().sum() == 0:
        raise ValueError("All transaction amounts are zero — check your data")

    min_date = pd.Timestamp("2000-01-01")
    max_date = pd.Timestamp.now() + pd.Timedelta(days=1)
    if df["date"].min() < min_date or df["date"].max() > max_date:
        raise ValueError(f"Dates out of valid range: {df['date'].min()} to {df['date'].max()}")


def parse_csv(content: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content))
    
    if _is_stripe_export(df):
        logger.info("DataIngestion: Stripe export detected — auto-normalizing")
        return _normalize_stripe(df)

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    df["date"] = pd.to_datetime(df["date"], format="mixed", utc=False)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0).astype(float)
    df["description"] = df["description"].fillna("").astype(str).str.strip()

    if "category" not in df.columns:
        df["category"] = df["description"].apply(_infer_category)

    if "currency" not in df.columns:
        df["currency"] = "USD"

    return df


def parse_json(content: bytes) -> pd.DataFrame:
    records = json.loads(content)
    if isinstance(records, dict) and "transactions" in records:
        records = records["transactions"]
    df = pd.DataFrame(records)
    # reuse CSV normalisation logic
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], format="mixed", utc=False)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0).astype(float)
    if "category" not in df.columns:
        df["category"] = df["description"].apply(_infer_category)
    if "currency" not in df.columns:
        df["currency"] = "USD"
    return df


async def ingest(
    content: bytes,
    file_type: str,
    run_id: Optional[UUID],
    db: AsyncSession,
) -> dict:
    """
    Main entry point called by the LangGraph workflow node.
    Returns structured ingestion summary written to graph state.
    """
    logger.info("DataIngestionAgent: parsing %s file (%d bytes)", file_type, len(content))

    validate_file(content, file_type)

    if file_type == "csv":
        df = parse_csv(content)
    elif file_type == "json":
        df = parse_json(content)

    validate_dataframe(df)

    records = []
    for _, row in df.iterrows():
        tx = Transaction(
            run_id=run_id,
            date=row["date"].to_pydatetime(),
            description=row["description"],
            category=row.get("category", "other"),
            amount=float(row["amount"]),
            currency=row.get("currency", "USD"),
        )
        db.add(tx)
        records.append(
            {
                "date": row["date"].isoformat(),
                "description": row["description"],
                "category": row.get("category", "other"),
                "amount": float(row["amount"]),
                "currency": row.get("currency", "USD"),
            }
        )

    await db.commit()
    logger.info("DataIngestionAgent: committed %d transactions", len(records))

    return {
        "total_transactions": len(records),
        "date_range": {
            "start": df["date"].min().isoformat(),
            "end": df["date"].max().isoformat(),
        },
        "categories": df["category"].value_counts().to_dict(),
        "transactions": records,
    }
