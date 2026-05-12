"""
Period Parser — Phase 3
========================
Converts natural-language period strings into (start, end) datetime pairs
suitable for SQLAlchemy range queries.

Supported formats:
    last_30d        — last 30 calendar days (rolling)
    last_7d         — last 7 days
    last_90d        — last 90 days
    this_month      — 1st of current month → now
    last_month      — full previous calendar month
    this_quarter    — 1st of current quarter → now
    last_quarter    — full previous quarter
    ytd             — Jan 1 of current year → now
    2024-Q1         — specific quarter  (Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec)
    2024-01         — specific month (YYYY-MM)
    2024-01-15:2024-03-31  — explicit range (ISO dates, colon-separated)
"""

import re
from datetime import datetime, timedelta, timezone, date
from typing import Optional

# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def _quarter_start_month(month: int) -> int:
    """Return the first month of the quarter that contains `month`."""
    return ((month - 1) // 3) * 3 + 1


# ── Main API ──────────────────────────────────────────────────────────────────

def parse_period(period_str: str) -> tuple[datetime, datetime]:
    """
    Convert a natural-language period string to a (start, end) UTC datetime pair.

    Both boundaries are timezone-aware (UTC).
    `start` is inclusive, `end` is inclusive (end of day for date-based ranges).

    Raises:
        ValueError: if the period string cannot be parsed.
    """
    p = period_str.strip().lower()
    now = _now()

    # ── Rolling day windows ───────────────────────────────────────────────────
    _rolling = {
        "last_7d":  7,
        "last_14d": 14,
        "last_30d": 30,
        "last_60d": 60,
        "last_90d": 90,
        "last_180d": 180,
        "last_365d": 365,
    }
    if p in _rolling:
        days = _rolling[p]
        start = _start_of_day(now - timedelta(days=days))
        return start, now

    # ── This month ────────────────────────────────────────────────────────────
    if p == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now

    # ── Last month ────────────────────────────────────────────────────────────
    if p == "last_month":
        first_of_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_of_prev = first_of_this - timedelta(seconds=1)
        first_of_prev = last_of_prev.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return first_of_prev, _end_of_day(last_of_prev)

    # ── This quarter ──────────────────────────────────────────────────────────
    if p == "this_quarter":
        qstart_month = _quarter_start_month(now.month)
        start = now.replace(month=qstart_month, day=1,
                            hour=0, minute=0, second=0, microsecond=0)
        return start, now

    # ── Last quarter ──────────────────────────────────────────────────────────
    if p == "last_quarter":
        qstart_month = _quarter_start_month(now.month)
        first_of_this_q = now.replace(month=qstart_month, day=1,
                                       hour=0, minute=0, second=0, microsecond=0)
        last_of_prev_q = first_of_this_q - timedelta(seconds=1)
        prev_qstart_month = _quarter_start_month(last_of_prev_q.month)
        start = last_of_prev_q.replace(month=prev_qstart_month, day=1,
                                        hour=0, minute=0, second=0, microsecond=0)
        return start, _end_of_day(last_of_prev_q)

    # ── Year to date ──────────────────────────────────────────────────────────
    if p == "ytd":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now

    # ── Specific quarter: 2024-Q1, 2024-q2, etc. ─────────────────────────────
    m = re.fullmatch(r"(\d{4})-q([1-4])", p)
    if m:
        year, q = int(m.group(1)), int(m.group(2))
        start_month = (q - 1) * 3 + 1
        end_month = start_month + 2
        start = datetime(year, start_month, 1, tzinfo=timezone.utc)
        # last day of end_month
        if end_month == 12:
            end = datetime(year, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
        else:
            first_of_next = datetime(year, end_month + 1, 1, tzinfo=timezone.utc)
            end = _end_of_day(first_of_next - timedelta(days=1))
        return start, end

    # ── Specific month: 2024-01 ───────────────────────────────────────────────
    m = re.fullmatch(r"(\d{4})-(\d{2})", period_str.strip())
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month in period string: {period_str!r}")
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)
        else:
            first_of_next = datetime(year, month + 1, 1, tzinfo=timezone.utc)
            end = _end_of_day(first_of_next - timedelta(days=1))
        return start, end

    # ── Explicit range: 2024-01-15:2024-03-31 ────────────────────────────────
    if ":" in period_str:
        parts = period_str.strip().split(":", 1)
        try:
            start = _start_of_day(
                datetime.fromisoformat(parts[0].strip()).replace(tzinfo=timezone.utc)
            )
            end = _end_of_day(
                datetime.fromisoformat(parts[1].strip()).replace(tzinfo=timezone.utc)
            )
            return start, end
        except ValueError:
            pass

    raise ValueError(
        f"Unrecognised period string: {period_str!r}. "
        "Supported: last_30d, last_7d, last_90d, this_month, last_month, "
        "this_quarter, last_quarter, ytd, '2024-Q1', '2024-01', '2024-01-01:2024-03-31'"
    )
