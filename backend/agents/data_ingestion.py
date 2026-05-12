"""
Agent 2 — Data Ingestion Agent
Parses CSV / JSON uploads, normalises transactions, writes to PostgreSQL.

Robust schema detection handles any real-world CSV format:
  - Standard format:  date, description, amount
  - Expenses format:  date_time, category, account, amount, currency
  - Transaction format: Date, Sender, Receiver, Amount (with embedded currency), Type
  - Stripe export:    id, description, created (utc), amount, currency, status, fee, net
  - Any other format: best-effort column mapping via alias tables
"""

import io
import json
import logging
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Transaction

logger = logging.getLogger("agent.ingestion")

# ── Category inference ────────────────────────────────────────────────────────

CATEGORY_MAP = {
    # Revenue signals
    "salary": "revenue",
    "invoice": "revenue",
    "refund": "revenue",
    "income": "revenue",
    "sales": "revenue",
    "revenue": "revenue",
    "deposit": "revenue",
    "credit": "revenue",
    "transfer in": "revenue",
    # Expense signals
    "payment": "expense",
    "rent": "expense",
    "utilities": "expense",
    "software": "expense",
    "travel": "expense",
    "marketing": "expense",
    "subscription": "expense",
    "fee": "expense",
    "purchase": "expense",
    "expense": "expense",
    "debit": "expense",
    "withdrawal": "expense",
    "food": "expense",
    "cafe": "expense",
    "transport": "expense",
    "health": "expense",
    "aws": "expense",
    "infrastructure": "expense",
}

EXPENSE_CATEGORIES = {
    "food", "cafe", "transport", "health", "rent", "utilities",
    "software", "travel", "marketing", "subscription", "entertainment",
    "shopping", "education", "insurance", "tax", "other expenses",
    "public transport", "groceries", "dining",
}

def _infer_category(text: str) -> str:
    """Infer revenue/expense from any text field."""
    if not text:
        return "other"
    t = text.lower().strip()
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in t:
            return cat
    return "other"

def _category_from_label(label: str) -> str:
    """Map a category label (from a category column) to revenue/expense/other."""
    if not label:
        return "other"
    l = label.lower().strip()
    if l in EXPENSE_CATEGORIES or any(k in l for k in ("expense", "fee", "payment", "purchase", "cost")):
        return "expense"
    if any(k in l for k in ("revenue", "income", "salary", "sales", "invoice", "refund", "deposit")):
        return "revenue"
    # Default: treat named categories as expenses (most personal finance data is expenses)
    return "expense"


# ── Amount cleaning ───────────────────────────────────────────────────────────

def _clean_amount(val) -> float:
    """
    Parse amount from any format:
      "100 Auric"  → 100.0
      "$1,234.56"  → 1234.56
      "(500.00)"   → -500.0   (accounting negative)
      "-1,200"     → -1200.0
      1200         → 1200.0
    """
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    # Accounting negatives: (500.00) → -500.00
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    # Strip everything except digits, minus, dot
    s = re.sub(r"[^\d\.\-]", "", s)
    if not s or s in ("-", "."):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


# ── Column alias tables ───────────────────────────────────────────────────────

# Maps canonical name → list of accepted aliases (all lowercase, underscored)
DATE_ALIASES = [
    "date", "date_time", "datetime", "transaction_date", "trans_date",
    "created", "created_at", "time", "timestamp", "posted_date",
    "value_date", "booking_date", "settlement_date",
]

DESCRIPTION_ALIASES = [
    "description", "desc", "memo", "narrative", "details", "note", "notes",
    "transaction_description", "trans_desc", "particulars", "reference",
    "remarks", "payee", "merchant", "name", "title", "label",
]

AMOUNT_ALIASES = [
    "amount", "value", "sum", "total", "net", "gross", "debit_amount",
    "credit_amount", "transaction_amount", "trans_amount", "price",
]

CATEGORY_ALIASES = [
    "category", "cat", "type", "transaction_type", "trans_type",
    "kind", "group", "classification", "tag", "tags",
]

CURRENCY_ALIASES = [
    "currency", "ccy", "curr", "iso_currency_code",
]


def _find_col(cols: set, aliases: list) -> Optional[str]:
    """Return the first alias that exists in cols, else None."""
    for alias in aliases:
        if alias in cols:
            return alias
    return None


# ── Stripe detection ──────────────────────────────────────────────────────────

STRIPE_COLUMNS = {"id", "description", "created (utc)", "amount", "currency", "status", "fee", "net"}

def _is_stripe_export(df: pd.DataFrame) -> bool:
    cols = {c.lower() for c in df.columns}
    return len(STRIPE_COLUMNS & cols) >= 5

def _normalize_stripe(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "created (utc)": "date",
        "description": "description",
        "net": "amount",
        "currency": "currency",
    }
    df = df.rename(columns={c: rename[c.lower()] for c in df.columns if c.lower() in rename})
    df = df[["date", "description", "amount", "currency"]].copy()
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_localize(None)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["category"] = df["description"].apply(_infer_category)
    return df[df["amount"] != 0].copy()


# ── Transaction-style format (Sender/Receiver/Amount with embedded currency) ──

def _is_transaction_format(cols: set) -> bool:
    """Detect formats like: Transaction ID, Date, Sender, Receiver, Amount, Fee, Type"""
    has_date = bool(_find_col(cols, DATE_ALIASES))
    has_amount = bool(_find_col(cols, AMOUNT_ALIASES))
    has_parties = bool({"sender", "receiver", "from", "to", "payer", "payee"} & cols)
    return has_date and has_amount and has_parties

def _normalize_transaction_format(df: pd.DataFrame, cols: set) -> pd.DataFrame:
    """Normalize sender/receiver style CSVs."""
    date_col = _find_col(cols, DATE_ALIASES)
    amount_col = _find_col(cols, AMOUNT_ALIASES)
    type_col = _find_col(cols, CATEGORY_ALIASES)

    # Build description from available party columns
    sender_col = next((c for c in ["sender", "from", "payer"] if c in cols), None)
    receiver_col = next((c for c in ["receiver", "to", "payee"] if c in cols), None)

    def _build_desc(row):
        parts = []
        if sender_col and pd.notna(row.get(sender_col)):
            parts.append(str(row[sender_col]))
        if receiver_col and pd.notna(row.get(receiver_col)):
            parts.append(f"→ {row[receiver_col]}")
        if type_col and pd.notna(row.get(type_col)):
            parts.append(f"({row[type_col]})")
        return " ".join(parts) if parts else "Transaction"

    result = pd.DataFrame()
    result["date"] = pd.to_datetime(df[date_col], format="mixed", utc=False, errors="coerce")
    result["amount"] = df[amount_col].apply(_clean_amount)
    result["description"] = df.apply(_build_desc, axis=1)

    # Infer category from type column or description
    if type_col:
        result["category"] = df[type_col].apply(
            lambda v: _category_from_label(str(v)) if pd.notna(v) else "other"
        )
    else:
        result["category"] = result["description"].apply(_infer_category)

    # Currency
    currency_col = _find_col(cols, CURRENCY_ALIASES)
    if currency_col:
        # Currency might be embedded in amount like "100 Auric" — use the column value
        result["currency"] = df[currency_col].fillna("USD").astype(str).str.strip()
        # Normalize known fictional/non-standard currencies to USD for financial math
        result["currency"] = result["currency"].apply(
            lambda c: c if len(c) == 3 and c.isupper() else "USD"
        )
    else:
        result["currency"] = "USD"

    return result[result["amount"] != 0].copy()


# ── Generic schema mapping ────────────────────────────────────────────────────

def _normalize_generic(df: pd.DataFrame, cols: set) -> pd.DataFrame:
    """
    Best-effort normalization for any CSV that has at least a date and amount column.
    Builds description from whatever text columns are available.
    """
    date_col = _find_col(cols, DATE_ALIASES)
    amount_col = _find_col(cols, AMOUNT_ALIASES)
    desc_col = _find_col(cols, DESCRIPTION_ALIASES)
    cat_col = _find_col(cols, CATEGORY_ALIASES)
    currency_col = _find_col(cols, CURRENCY_ALIASES)

    result = pd.DataFrame()
    result["date"] = pd.to_datetime(df[date_col], format="mixed", utc=False, errors="coerce")
    result["amount"] = df[amount_col].apply(_clean_amount)

    # Build description
    if desc_col:
        result["description"] = df[desc_col].fillna("").astype(str).str.strip()
    elif cat_col:
        # Use category as description if no description column
        result["description"] = df[cat_col].fillna("").astype(str).str.strip()
    else:
        # Last resort: concatenate all string columns
        str_cols = [c for c in df.columns if df[c].dtype == object and c not in (date_col, amount_col, currency_col)]
        if str_cols:
            result["description"] = df[str_cols].fillna("").astype(str).agg(" | ".join, axis=1).str.strip()
        else:
            result["description"] = "Transaction"

    # Category
    if cat_col:
        result["category"] = df[cat_col].apply(
            lambda v: _category_from_label(str(v)) if pd.notna(v) else "other"
        )
    else:
        result["category"] = result["description"].apply(_infer_category)

    # Currency
    if currency_col:
        result["currency"] = df[currency_col].fillna("USD").astype(str).str.strip()
        result["currency"] = result["currency"].apply(
            lambda c: c if len(c) == 3 and c.isupper() else "USD"
        )
    else:
        result["currency"] = "USD"

    return result.copy()


# ── Debit/Credit split columns ────────────────────────────────────────────────

def _has_debit_credit_split(cols: set) -> bool:
    """Detect bank statements with separate debit/credit columns."""
    has_debit = bool({"debit", "debit_amount", "withdrawals", "withdrawal"} & cols)
    has_credit = bool({"credit", "credit_amount", "deposits", "deposit"} & cols)
    return has_debit or has_credit

def _normalize_debit_credit(df: pd.DataFrame, cols: set) -> pd.DataFrame:
    """Merge debit/credit columns into a single signed amount."""
    debit_col = next((c for c in ["debit", "debit_amount", "withdrawals", "withdrawal"] if c in cols), None)
    credit_col = next((c for c in ["credit", "credit_amount", "deposits", "deposit"] if c in cols), None)

    if debit_col and credit_col:
        debit = df[debit_col].apply(_clean_amount).fillna(0.0)
        credit = df[credit_col].apply(_clean_amount).fillna(0.0)
        df = df.copy()
        df["amount"] = credit - debit  # credits positive, debits negative
    elif debit_col:
        df = df.copy()
        df["amount"] = -df[debit_col].apply(_clean_amount).fillna(0.0)
    elif credit_col:
        df = df.copy()
        df["amount"] = df[credit_col].apply(_clean_amount).fillna(0.0)

    # Now normalize as generic
    new_cols = {c.lower().replace(" ", "_") for c in df.columns}
    return _normalize_generic(df, new_cols)


# ── Validation ────────────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROW_COUNT = 100_000

def validate_file(content: bytes, file_type: str):
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large: {len(content) // 1024}KB > 10MB limit")
    if file_type not in ("csv", "json"):
        raise ValueError(f"Unsupported file type: {file_type}. Use csv or json.")

def validate_dataframe(df: pd.DataFrame):
    if len(df) > MAX_ROW_COUNT:
        raise ValueError(f"Too many rows: {len(df)} > {MAX_ROW_COUNT} limit")
    if len(df) < 2:
        raise ValueError(f"Too few transactions: need at least 2 rows, got {len(df)}")
    if df["amount"].abs().sum() == 0:
        raise ValueError("All transaction amounts are zero — check your data format")

    # Drop rows with unparseable dates
    bad_dates = df["date"].isna().sum()
    if bad_dates > 0:
        logger.warning("DataIngestion: dropping %d rows with unparseable dates", bad_dates)
        df.drop(df[df["date"].isna()].index, inplace=True)

    if len(df) == 0:
        raise ValueError("No rows with valid dates found")

    min_date = pd.Timestamp("1990-01-01")
    max_date = pd.Timestamp.now() + pd.Timedelta(days=365)
    valid = df[(df["date"] >= min_date) & (df["date"] <= max_date)]
    if len(valid) == 0:
        raise ValueError(f"All dates are out of valid range (1990–future)")
    if len(valid) < len(df):
        logger.warning("DataIngestion: dropping %d rows with out-of-range dates", len(df) - len(valid))
        df.drop(df[~df.index.isin(valid.index)].index, inplace=True)


# ── Main CSV parser ───────────────────────────────────────────────────────────

def parse_csv(content: bytes) -> pd.DataFrame:
    # Try multiple encodings
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=encoding, on_bad_lines="skip")
            break
        except Exception:
            continue
    else:
        raise ValueError("Could not decode CSV file — try saving as UTF-8")

    if df.empty or len(df.columns) < 2:
        raise ValueError("CSV appears empty or has fewer than 2 columns")

    # ── Stripe detection (before column normalisation) ────────────────────────
    if _is_stripe_export(df):
        logger.info("DataIngestion: Stripe export detected — auto-normalizing")
        return _normalize_stripe(df)

    # Normalise column names: strip whitespace, lowercase, replace spaces with _
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    cols = set(df.columns)

    logger.info("DataIngestion: detected columns: %s", list(df.columns))

    # ── Debit/Credit split format ─────────────────────────────────────────────
    if _has_debit_credit_split(cols) and not _find_col(cols, AMOUNT_ALIASES):
        logger.info("DataIngestion: debit/credit split format detected")
        return _normalize_debit_credit(df, cols)

    # ── Must have at least a date and an amount ───────────────────────────────
    date_col = _find_col(cols, DATE_ALIASES)
    amount_col = _find_col(cols, AMOUNT_ALIASES)

    if not date_col:
        raise ValueError(
            f"Could not find a date column. Detected columns: {sorted(cols)}. "
            "Expected one of: date, date_time, transaction_date, created, timestamp, etc."
        )
    if not amount_col:
        raise ValueError(
            f"Could not find an amount column. Detected columns: {sorted(cols)}. "
            "Expected one of: amount, value, net, total, debit, credit, etc."
        )

    # ── Transaction format (Sender/Receiver) ──────────────────────────────────
    if _is_transaction_format(cols):
        logger.info("DataIngestion: sender/receiver transaction format detected")
        return _normalize_transaction_format(df, cols)

    # ── Generic mapping ───────────────────────────────────────────────────────
    logger.info("DataIngestion: using generic column mapping")
    return _normalize_generic(df, cols)


# ── JSON parser ───────────────────────────────────────────────────────────────

def parse_json(content: bytes) -> pd.DataFrame:
    try:
        records = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    if isinstance(records, dict):
        # Try common wrapper keys
        for key in ("transactions", "data", "records", "items", "results"):
            if key in records:
                records = records[key]
                break
        else:
            # Single object — wrap in list
            records = [records]

    if not isinstance(records, list) or len(records) == 0:
        raise ValueError("JSON must contain a list of transaction objects")

    df = pd.DataFrame(records)
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    cols = set(df.columns)

    date_col = _find_col(cols, DATE_ALIASES)
    amount_col = _find_col(cols, AMOUNT_ALIASES)

    if not date_col:
        raise ValueError(f"JSON missing date field. Found: {sorted(cols)}")
    if not amount_col:
        raise ValueError(f"JSON missing amount field. Found: {sorted(cols)}")

    return _normalize_generic(df, cols)


# ── Main entry point ──────────────────────────────────────────────────────────

async def ingest(
    content: bytes,
    file_type: str,
    run_id: Optional[UUID],
    db: AsyncSession,
    business_id: Optional[UUID] = None,
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
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    # Ensure required columns exist after normalisation
    for col in ("date", "amount", "description", "category", "currency"):
        if col not in df.columns:
            raise ValueError(f"Internal error: normalised DataFrame missing column '{col}'")

    # Clean up
    df = df.copy()
    df["description"] = df["description"].fillna("").astype(str).str.strip()
    df["description"] = df["description"].replace("", "Transaction")
    df["amount"] = df["amount"].fillna(0.0).astype(float)
    df = df[df["amount"] != 0].copy()  # drop zero-amount rows

    validate_dataframe(df)

    logger.info(
        "DataIngestionAgent: parsed %d rows, date range %s → %s, categories: %s",
        len(df),
        df["date"].min().date(),
        df["date"].max().date(),
        df["category"].value_counts().to_dict(),
    )

    records_dicts = df.to_dict("records")
    tx_objects = [
        Transaction(
            run_id=run_id,
            business_id=business_id,
            date=row["date"].to_pydatetime() if hasattr(row["date"], "to_pydatetime") else row["date"],
            description=str(row["description"]),
            category=str(row.get("category", "other")),
            amount=float(row["amount"]),
            currency=str(row.get("currency", "USD")),
        )
        for row in records_dicts
    ]
    db.add_all(tx_objects)

    records = [
        {
            "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
            "description": str(row["description"]),
            "category": str(row.get("category", "other")),
            "amount": float(row["amount"]),
            "currency": str(row.get("currency", "USD")),
        }
        for row in records_dicts
    ]

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
