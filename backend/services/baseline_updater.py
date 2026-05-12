"""
Baseline Updater Service — Phase 2
===================================
Called after every successful ingestion run. Updates the CategoryBaseline table
using an Exponentially Weighted Moving Average (EWMA) so the anomaly detector
can compare each category's spending against its own seasonal history rather
than the global Z-score of all transactions.

EWMA update rule (alpha=0.3):
    new_ewma  = alpha * new_value + (1 - alpha) * old_ewma
    new_ewmstd = sqrt(alpha * (new_value - new_ewma)^2 + (1 - alpha) * old_ewmstd^2)

For the first 3 observations we use simple mean / std (insufficient data for EWMA).
"""

import logging
import math
import uuid as uuid_mod
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CategoryBaseline

logger = logging.getLogger("services.baseline_updater")

# EWMA decay factor — higher alpha = faster adaptation to new data
ALPHA = 0.3
# Minimum observations before switching from simple mean to EWMA
MIN_OBS_FOR_EWMA = 3


def _parse_date(date_val) -> Optional[datetime]:
    """Safely parse a date value that may be a str, datetime, or pandas Timestamp."""
    if date_val is None:
        return None
    if isinstance(date_val, datetime):
        return date_val
    try:
        # Handle ISO strings from df["date"].isoformat()
        return datetime.fromisoformat(str(date_val).replace("Z", "+00:00"))
    except Exception:
        return None


async def update_baselines_for_run(
    db: AsyncSession,
    business_id: UUID,
    transactions: list[dict],
) -> None:
    """
    Main entry point — call after every successful ingestion.

    Groups transactions by (category, month_of_year), aggregates spend,
    then upserts each CategoryBaseline row with the new EWMA values.
    """
    if not transactions:
        logger.debug("[BaselineUpdater] No transactions — skipping.")
        return

    # Aggregate: sum absolute spend per (category, month)
    category_month_totals: dict[tuple[str, int], float] = defaultdict(float)
    for tx in transactions:
        parsed = _parse_date(tx.get("date"))
        if parsed is None:
            continue
        month = parsed.month
        category = tx.get("category") or "other"
        category_month_totals[(category, month)] += abs(float(tx.get("amount", 0)))

    for (category, month), total in category_month_totals.items():
        await _upsert_baseline(db, business_id, category, month, total)

    await db.commit()
    logger.info(
        "[BaselineUpdater] Updated %d category-month baselines for business_id=%s",
        len(category_month_totals),
        business_id,
    )


async def _upsert_baseline(
    db: AsyncSession,
    business_id: UUID,
    category: str,
    month: int,
    new_amount: float,
    alpha: float = ALPHA,
) -> None:
    """
    Fetch or create a CategoryBaseline row and apply the EWMA update.
    """
    result = await db.execute(
        select(CategoryBaseline).where(
            CategoryBaseline.business_id == business_id,
            CategoryBaseline.category == category,
            CategoryBaseline.month_of_year == month,
        )
    )
    baseline = result.scalar_one_or_none()

    if baseline is None:
        # First observation for this (category, month) — initialise
        baseline = CategoryBaseline(
            id=uuid_mod.uuid4(),
            business_id=business_id,
            category=category,
            month_of_year=month,
            ewma=new_amount,
            ewmstd=abs(new_amount) * 0.3,  # conservative 30% std as prior
            n_observations=1,
            last_updated=datetime.now(timezone.utc),
        )
        db.add(baseline)
        logger.debug(
            "[BaselineUpdater] Created baseline category=%s month=%d ewma=%.2f",
            category, month, new_amount,
        )
        return

    n = baseline.n_observations

    if n < MIN_OBS_FOR_EWMA:
        # Simple mean update (not enough data for EWMA)
        old_mean = baseline.ewma
        new_mean = (old_mean * n + new_amount) / (n + 1)
        # Running variance: Welford's method
        old_std = baseline.ewmstd
        delta = new_amount - old_mean
        delta2 = new_amount - new_mean
        new_variance = ((old_std ** 2) * n + delta * delta2) / (n + 1)
        baseline.ewma = new_mean
        baseline.ewmstd = math.sqrt(max(new_variance, 1e-6))
    else:
        # EWMA update
        old_ewma = baseline.ewma
        new_ewma = alpha * new_amount + (1 - alpha) * old_ewma
        old_ewmstd = baseline.ewmstd
        new_ewmstd = math.sqrt(
            alpha * (new_amount - new_ewma) ** 2 + (1 - alpha) * (old_ewmstd ** 2)
        )
        baseline.ewma = new_ewma
        baseline.ewmstd = max(new_ewmstd, 1e-6)

    baseline.n_observations = n + 1
    baseline.last_updated = datetime.now(timezone.utc)

    logger.debug(
        "[BaselineUpdater] Updated baseline category=%s month=%d n=%d ewma=%.2f ewmstd=%.2f",
        category, month, baseline.n_observations, baseline.ewma, baseline.ewmstd,
    )
