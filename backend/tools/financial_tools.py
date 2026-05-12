"""
Financial Tools — Phase 3 / Tool Registry
==========================================
Six standalone async tool functions used by the Chat Agent (Phase 4) and the
Analysis Agent (Phase 5).  Each function takes an `AsyncSession` + `business_id`
and returns a plain dict so it can be serialised to JSON for the LLM or the REST API.

Tools
-----
1. compute_pnl          — revenue / expenses / margin for a period
2. compute_runway       — months of cash runway at current burn rate
3. query_transactions   — flexible filtered transaction explorer
4. compare_periods      — period-over-period metric comparison
5. find_anomalies       — Z-score + optional EWMA-baseline anomaly detection
6. get_category_trends  — per-category spending trends over N periods
"""

import logging
import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import numpy as np
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CategoryBaseline, Transaction
from tools.period_parser import parse_period

logger = logging.getLogger("tools.financial_tools")


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _fetch_transactions(
    db: AsyncSession,
    business_id: Optional[UUID],
    start: datetime,
    end: datetime,
    category: Optional[str] = None,
) -> list[Transaction]:
    """Return Transaction ORM rows for the given business_id and date range."""
    filters = [
        Transaction.date >= start,
        Transaction.date <= end,
    ]
    if business_id is not None:
        filters.append(Transaction.business_id == business_id)
    if category is not None:
        filters.append(Transaction.category == category)

    result = await db.execute(
        select(Transaction).where(and_(*filters)).order_by(Transaction.date)
    )
    return result.scalars().all()


def _tx_to_dict(tx: Transaction) -> dict:
    return {
        "id": str(tx.id),
        "date": tx.date.isoformat() if tx.date else None,
        "description": tx.description,
        "category": tx.category,
        "amount": tx.amount,
        "currency": tx.currency,
        "is_anomaly": tx.is_anomaly,
    }


# ── Tool 1: compute_pnl ───────────────────────────────────────────────────────

async def compute_pnl(
    db: AsyncSession,
    business_id: Optional[UUID],
    period: str = "last_30d",
) -> dict:
    """
    Compute Profit & Loss for a given period.

    Returns:
        revenue, expenses, gross_profit, net_profit (after ~25% tax estimate),
        margin_pct, period_start, period_end, transaction_count
    """
    start, end = parse_period(period)
    txns = await _fetch_transactions(db, business_id, start, end)

    revenue = sum(t.amount for t in txns if t.amount > 0)
    expenses = sum(abs(t.amount) for t in txns if t.amount < 0)
    gross_profit = revenue - expenses
    margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0.0

    # Rough net profit: apply configurable tax rate (default 25 %)
    import os
    tax_rate = float(os.getenv("TAX_RATE_PCT", "25")) / 100
    net_profit = gross_profit * (1 - tax_rate)

    # Category breakdown
    cat_revenue: dict[str, float] = {}
    cat_expenses: dict[str, float] = {}
    for t in txns:
        cat = t.category or "other"
        if t.amount > 0:
            cat_revenue[cat] = cat_revenue.get(cat, 0) + t.amount
        else:
            cat_expenses[cat] = cat_expenses.get(cat, 0) + abs(t.amount)

    return {
        "period": period,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "revenue": round(revenue, 2),
        "expenses": round(expenses, 2),
        "gross_profit": round(gross_profit, 2),
        "net_profit": round(net_profit, 2),
        "margin_pct": round(margin_pct, 2),
        "transaction_count": len(txns),
        "revenue_by_category": {k: round(v, 2) for k, v in cat_revenue.items()},
        "expenses_by_category": {k: round(v, 2) for k, v in cat_expenses.items()},
    }


# ── Tool 2: compute_runway ────────────────────────────────────────────────────

async def compute_runway(
    db: AsyncSession,
    business_id: Optional[UUID],
    additional_monthly_cost: float = 0.0,
) -> dict:
    """
    Calculate months of cash runway at current burn rate.

    Data-aware: uses the actual date range of transactions, not today's date.
    Uses the last 3 months of available data to estimate monthly burn via EWMA (α=0.4).
    """
    from sqlalchemy import func as sqlfunc
    from db.models import Transaction as TxModel
    from datetime import timezone
    from dateutil.relativedelta import relativedelta

    # Detect actual data range
    date_result = await db.execute(
        select(
            sqlfunc.min(TxModel.date).label("min_date"),
            sqlfunc.max(TxModel.date).label("max_date"),
        ).where(TxModel.business_id == business_id)
    )
    date_row = date_result.one_or_none()
    data_max = date_row.max_date if date_row else None

    if data_max is None:
        return {
            "months_of_runway": None,
            "monthly_burn": 0.0,
            "monthly_revenue": 0.0,
            "net_burn": 0.0,
            "warning": "No transaction data found",
            "cash_balance_estimate": None,
        }

    # Make timezone-aware
    if data_max.tzinfo is None:
        data_max = data_max.replace(tzinfo=timezone.utc)

    # Anchor to the last month of data
    anchor = data_max.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    pnl_months = []
    for i in range(2, -1, -1):  # 3 months ending at anchor
        m_start = anchor - relativedelta(months=i)
        m_end = (m_start + relativedelta(months=1)) - relativedelta(seconds=1)
        txns = await _fetch_transactions(db, business_id, m_start, m_end)
        rev = sum(t.amount for t in txns if t.amount > 0)
        exp = sum(abs(t.amount) for t in txns if t.amount < 0)
        pnl_months.append({"revenue": rev, "expenses": exp, "burn": max(exp - rev, 0)})

    # Also get last 90 days of data relative to data_max for cash balance estimate
    start90 = data_max - relativedelta(days=90)
    txns90 = await _fetch_transactions(db, business_id, start90, data_max)

    if not pnl_months or all(m["revenue"] == 0 and m["expenses"] == 0 for m in pnl_months):
        return {
            "months_of_runway": None,
            "monthly_burn": 0.0,
            "monthly_revenue": 0.0,
            "net_burn": 0.0,
            "warning": "Insufficient data to compute runway",
            "cash_balance_estimate": None,
        }

    # EWMA burn rate (α=0.4, most recent month weighted most)
    alpha = 0.4
    ewma_burn = pnl_months[0]["burn"]
    ewma_rev = pnl_months[0]["revenue"]
    for m in pnl_months[1:]:
        ewma_burn = alpha * m["burn"] + (1 - alpha) * ewma_burn
        ewma_rev = alpha * m["revenue"] + (1 - alpha) * ewma_rev

    effective_burn = ewma_burn + additional_monthly_cost
    net_burn = max(effective_burn - ewma_rev, 0)

    # Approximate cash balance from net revenue accumulation over last 90 days
    total_net = sum(t.amount for t in txns90) if txns90 else 0.0
    cash_estimate = max(total_net, 0)

    months_of_runway = (cash_estimate / net_burn) if net_burn > 0 else None

    warning = None
    if months_of_runway is not None and months_of_runway < 3:
        warning = f"⚠️ Critical: only {months_of_runway:.1f} months of runway remaining."
    elif months_of_runway is not None and months_of_runway < 6:
        warning = f"⚠️ Warning: {months_of_runway:.1f} months of runway — consider fundraising."

    return {
        "months_of_runway": round(months_of_runway, 1) if months_of_runway is not None else None,
        "monthly_burn": round(ewma_burn, 2),
        "monthly_revenue": round(ewma_rev, 2),
        "additional_monthly_cost": additional_monthly_cost,
        "net_burn": round(net_burn, 2),
        "cash_balance_estimate": round(cash_estimate, 2),
        "warning": warning,
    }


# ── Tool 3: query_transactions ────────────────────────────────────────────────

async def query_transactions(
    db: AsyncSession,
    business_id: Optional[UUID],
    period: str = "last_30d",
    category: Optional[str] = None,
    limit: int = 20,
    aggregate: Optional[str] = None,   # "sum" | "count" | "avg" | None
    group_by: Optional[str] = None,    # "category" | "month" | None
) -> dict:
    """
    Flexible transaction explorer for the Chat Agent.

    Modes:
    - aggregate=None  → returns a list of individual transactions (up to `limit`)
    - aggregate="sum" + group_by="category" → total spend per category
    - aggregate="sum" + group_by="month"    → monthly totals
    - aggregate="count"                     → count of matching transactions
    - aggregate="avg"                       → average transaction amount
    """
    start, end = parse_period(period)
    txns = await _fetch_transactions(db, business_id, start, end, category=category)

    if not txns:
        return {"transactions": [], "total": 0, "period": period,
                "aggregate": aggregate, "group_by": group_by}

    amounts = [t.amount for t in txns]

    # No aggregation — return raw rows (trimmed to limit)
    if aggregate is None and group_by is None:
        rows = [_tx_to_dict(t) for t in txns[-limit:]]
        return {
            "transactions": rows,
            "total": len(txns),
            "shown": len(rows),
            "period": period,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        }

    # Aggregation modes
    if aggregate == "count":
        return {"count": len(txns), "period": period, "category": category}

    if aggregate == "avg":
        return {
            "avg_amount": round(sum(amounts) / len(amounts), 2),
            "count": len(txns),
            "period": period,
        }

    # Sum with group_by
    if aggregate == "sum":
        if group_by == "category":
            cats: dict[str, float] = {}
            for t in txns:
                cats[t.category or "other"] = cats.get(t.category or "other", 0) + t.amount
            return {
                "group_by": "category",
                "data": {k: round(v, 2) for k, v in sorted(cats.items(), key=lambda x: -abs(x[1]))},
                "period": period,
            }

        if group_by == "month":
            months: dict[str, float] = {}
            for t in txns:
                key = t.date.strftime("%Y-%m") if t.date else "unknown"
                months[key] = months.get(key, 0) + t.amount
            return {
                "group_by": "month",
                "data": {k: round(v, 2) for k, v in sorted(months.items())},
                "period": period,
            }

        # Plain sum
        return {"sum": round(sum(amounts), 2), "count": len(txns), "period": period}

    # Fallback: return raw
    return {"transactions": [_tx_to_dict(t) for t in txns[:limit]], "total": len(txns)}


# ── Tool 4: compare_periods ───────────────────────────────────────────────────

async def compare_periods(
    db: AsyncSession,
    business_id: Optional[UUID],
    period_a: str = "this_month",
    period_b: str = "last_month",
    metric: str = "revenue",  # "revenue" | "expenses" | "net_profit" | "margin_pct"
) -> dict:
    """
    Compare a financial metric across two time periods.

    Returns:
        metric, period_a_value, period_b_value, change_abs, change_pct, interpretation
    """
    pnl_a = await compute_pnl(db, business_id, period_a)
    pnl_b = await compute_pnl(db, business_id, period_b)

    val_a = pnl_a.get(metric, 0) or 0
    val_b = pnl_b.get(metric, 0) or 0

    change_abs = val_a - val_b
    change_pct = ((change_abs / abs(val_b)) * 100) if val_b != 0 else None

    # Human interpretation
    direction = "increased" if change_abs > 0 else "decreased" if change_abs < 0 else "unchanged"
    if change_pct is not None:
        interpretation = (
            f"{metric.replace('_', ' ').title()} {direction} by "
            f"{abs(change_pct):.1f}% from {period_b} to {period_a}."
        )
    else:
        interpretation = f"No data in {period_b} to compare against."

    return {
        "metric": metric,
        "period_a": period_a,
        "period_b": period_b,
        "period_a_value": round(val_a, 2),
        "period_b_value": round(val_b, 2),
        "change_abs": round(change_abs, 2),
        "change_pct": round(change_pct, 2) if change_pct is not None else None,
        "interpretation": interpretation,
    }


# ── Tool 5: find_anomalies ────────────────────────────────────────────────────

async def find_anomalies(
    db: AsyncSession,
    business_id: Optional[UUID],
    period: str = "last_30d",
    use_baselines: bool = True,
    z_threshold: float = 2.5,
) -> dict:
    """
    Detect anomalous transactions using Z-score + optional EWMA category baselines.

    Data-aware: if the period resolves to zero transactions (e.g. "last_30d" when
    data is historical), automatically falls back to the last 30 days of actual data.
    """
    start, end = parse_period(period)
    txns = await _fetch_transactions(db, business_id, start, end)

    # Data-aware fallback: if no transactions in the requested period, use last 30 days of actual data
    if len(txns) < 4:
        from sqlalchemy import func as sqlfunc
        from db.models import Transaction as TxModel
        from dateutil.relativedelta import relativedelta

        date_result = await db.execute(
            select(
                sqlfunc.max(TxModel.date).label("max_date"),
            ).where(TxModel.business_id == business_id)
        )
        date_row = date_result.one_or_none()
        data_max = date_row.max_date if date_row else None

        if data_max is not None:
            from datetime import timezone
            if data_max.tzinfo is None:
                data_max = data_max.replace(tzinfo=timezone.utc)
            fallback_start = data_max - relativedelta(days=30)
            txns = await _fetch_transactions(db, business_id, fallback_start, data_max)

    if len(txns) < 4:
        return {"anomalies": [], "total_flagged": 0, "method_used": "insufficient_data"}

    anomalies = []

    if use_baselines and business_id is not None:
        baselines_result = await db.execute(
            select(CategoryBaseline).where(CategoryBaseline.business_id == business_id)
        )
        baselines = baselines_result.scalars().all()
        baseline_map: dict[tuple[str, int], CategoryBaseline] = {
            (b.category, b.month_of_year): b for b in baselines
        }

        if baseline_map:
            for tx in txns:
                cat = tx.category or "other"
                month = tx.date.month if tx.date else 0
                bl = baseline_map.get((cat, month))
                if bl and bl.n_observations >= 3:
                    z = abs((abs(tx.amount) - bl.ewma) / max(bl.ewmstd, 1e-6))
                    if z > z_threshold:
                        anomalies.append({
                            **_tx_to_dict(tx),
                            "z_score": round(z, 3),
                            "ewma_baseline": round(bl.ewma, 2),
                            "ewmstd": round(bl.ewmstd, 2),
                            "detection_method": "ewma_baseline",
                        })
            if anomalies:
                return {
                    "anomalies": sorted(anomalies, key=lambda x: -x["z_score"])[:20],
                    "total_flagged": len(anomalies),
                    "method_used": "ewma_baseline",
                    "period": period,
                }

    # Fallback: global Z-score
    amounts = np.array([abs(t.amount) for t in txns], dtype=float)
    mean = amounts.mean()
    std = amounts.std()

    if std < 1e-6:
        return {"anomalies": [], "total_flagged": 0, "method_used": "global_zscore_uniform_data"}

    q1, q3 = np.percentile(amounts, 25), np.percentile(amounts, 75)
    iqr = q3 - q1

    for i, tx in enumerate(txns):
        amt = abs(tx.amount)
        z = abs((amt - mean) / std)
        iqr_flag = amt < (q1 - 1.5 * iqr) or amt > (q3 + 1.5 * iqr)
        if z > z_threshold or iqr_flag:
            anomalies.append({
                **_tx_to_dict(tx),
                "z_score": round(float(z), 3),
                "detection_method": "global_zscore",
            })

    return {
        "anomalies": sorted(anomalies, key=lambda x: -x["z_score"])[:20],
        "total_flagged": len(anomalies),
        "method_used": "global_zscore",
        "period": period,
    }


# ── Tool 6: get_category_trends ───────────────────────────────────────────────

async def get_category_trends(
    db: AsyncSession,
    business_id: Optional[UUID],
    category: Optional[str] = None,
    periods: int = 6,
) -> dict:
    """
    Get spending trends per category over the last N calendar months.

    Returns a list of {period, category, total, change_pct} records,
    sorted by period ascending so the chart can plot them directly.
    """
    from datetime import date
    from dateutil.relativedelta import relativedelta  # type: ignore[import]

    now = datetime.now(timezone.utc)
    results = []

    # Build month list: last `periods` complete months + current partial month
    month_starts = []
    for i in range(periods - 1, -1, -1):
        m_start = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                   - relativedelta(months=i))
        month_starts.append(m_start)

    prev_totals: dict[str, float] = {}  # category → last month total

    for m_start in month_starts:
        m_end = (m_start + relativedelta(months=1)) - relativedelta(seconds=1)
        if m_end > now:
            m_end = now

        txns = await _fetch_transactions(db, business_id, m_start, m_end, category=category)

        # Sum by category
        cat_totals: dict[str, float] = {}
        for t in txns:
            cat = t.category or "other"
            cat_totals[cat] = cat_totals.get(cat, 0) + abs(t.amount)

        period_label = m_start.strftime("%Y-%m")

        # If filtering by category, only emit that category
        cats_to_emit = [category] if category else list(cat_totals.keys())

        for cat in cats_to_emit:
            total = cat_totals.get(cat, 0.0)
            prev = prev_totals.get(cat)
            change_pct = None
            if prev is not None and prev > 0:
                change_pct = round((total - prev) / prev * 100, 2)
            results.append({
                "period": period_label,
                "category": cat,
                "total": round(total, 2),
                "change_pct": change_pct,
            })

        # Update prev totals for next iteration
        for cat, total in cat_totals.items():
            prev_totals[cat] = total

    return {
        "trends": results,
        "periods": periods,
        "category_filter": category,
    }
