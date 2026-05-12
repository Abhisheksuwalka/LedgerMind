"""
Business Profile Service — Phase 2
=====================================
Manages the single-tenant BusinessProfile row.
For the MVP there is exactly ONE profile for the entire app.

This service:
  1. Creates the profile on first use (get_or_create_profile)
  2. Updates accumulated stats after every pipeline run
     (total_uploads, date_range, EWMA revenue/expenses/burn, health score history)
"""

import logging
import uuid as uuid_mod
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BusinessProfile

logger = logging.getLogger("services.profile_service")

# Singleton profile name — change via env in multi-tenant future
DEFAULT_PROFILE_NAME = "My Business"


async def get_or_create_profile(db: AsyncSession) -> BusinessProfile:
    """
    Return the single BusinessProfile row, creating it if it doesn't exist yet.
    Safe to call concurrently — uses SELECT-then-INSERT pattern with commit.
    """
    result = await db.execute(select(BusinessProfile).limit(1))
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = BusinessProfile(
            id=uuid_mod.uuid4(),
            name=DEFAULT_PROFILE_NAME,
            created_at=datetime.now(timezone.utc),
            total_uploads=0,
            health_score=50.0,
            health_score_history=[],
            avg_monthly_revenue=0.0,
            avg_monthly_expenses=0.0,
            avg_monthly_burn=0.0,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        logger.info("[ProfileService] Created BusinessProfile id=%s", profile.id)

    return profile


async def get_profile(db: AsyncSession, business_id: UUID) -> Optional[BusinessProfile]:
    """Fetch a profile by ID. Returns None if not found."""
    result = await db.execute(
        select(BusinessProfile).where(BusinessProfile.id == business_id)
    )
    return result.scalar_one_or_none()


async def update_profile_after_run(
    db: AsyncSession,
    business_id: UUID,
    ingestion_result: dict,
    pnl_result: Optional[dict] = None,
) -> None:
    """
    Update the BusinessProfile after a successful pipeline run.

    Updates:
    - total_uploads counter
    - first_data_date / latest_data_date from ingestion date range
    - avg_monthly_revenue / avg_monthly_expenses / avg_monthly_burn (EWMA, α=0.3)
    - health_score + health_score_history (rolling window, last 90 entries)
    """
    profile = await get_profile(db, business_id)
    if profile is None:
        logger.warning("[ProfileService] Profile %s not found — skipping update.", business_id)
        return

    alpha = 0.3  # EWMA decay for financial metrics

    # ── Upload count ──────────────────────────────────────────────────────────
    profile.total_uploads = (profile.total_uploads or 0) + 1

    # ── Date range ────────────────────────────────────────────────────────────
    date_range = ingestion_result.get("date_range", {})
    start_str = date_range.get("start")
    end_str = date_range.get("end")

    if start_str:
        try:
            start_dt = datetime.fromisoformat(str(start_str).replace("Z", "+00:00"))
            if profile.first_data_date is None or start_dt < profile.first_data_date:
                profile.first_data_date = start_dt
        except Exception:
            pass

    if end_str:
        try:
            end_dt = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
            if profile.latest_data_date is None or end_dt > profile.latest_data_date:
                profile.latest_data_date = end_dt
        except Exception:
            pass

    # ── Revenue / expense / burn (from PnL result) ────────────────────────────
    if pnl_result:
        new_rev = float(pnl_result.get("revenue", 0) or 0)
        new_exp = float(pnl_result.get("expenses", 0) or 0)
        new_burn = max(new_exp - new_rev, 0)  # burn = net negative cash flow

        if profile.avg_monthly_revenue == 0:
            # First data point — initialise
            profile.avg_monthly_revenue = new_rev
            profile.avg_monthly_expenses = new_exp
            profile.avg_monthly_burn = new_burn
        else:
            profile.avg_monthly_revenue = (
                alpha * new_rev + (1 - alpha) * profile.avg_monthly_revenue
            )
            profile.avg_monthly_expenses = (
                alpha * new_exp + (1 - alpha) * profile.avg_monthly_expenses
            )
            profile.avg_monthly_burn = (
                alpha * new_burn + (1 - alpha) * profile.avg_monthly_burn
            )

        # ── Health score update ────────────────────────────────────────────────
        new_health = float(pnl_result.get("health_score", profile.health_score) or profile.health_score)
        profile.health_score = new_health

        # Append to history, keep last 90 entries (≈3 months of daily uploads)
        history = list(profile.health_score_history or [])
        history.append({
            "date": datetime.now(timezone.utc).isoformat(),
            "score": new_health,
        })
        profile.health_score_history = history[-90:]

    await db.commit()
    logger.info(
        "[ProfileService] Updated business_id=%s  uploads=%d  health=%.1f",
        business_id,
        profile.total_uploads,
        profile.health_score,
    )
