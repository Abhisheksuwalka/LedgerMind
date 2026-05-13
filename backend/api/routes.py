"""
FastAPI routes — public API surface for the LedgerMind platform.
POST /run returns 202 immediately; pipeline runs as a background asyncio task.
"""

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.models import Alert, AuditLog, FinancialReport, PipelineRun, RunStatus, get_db, AsyncSessionLocal
from graph.workflow import FinAgentState, build_graph
from api.auth import verify_api_key, verify_internal_secret

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


def _alert_dedupe_key(
    *,
    business_id,
    alert_type: str,
    title: str,
    message: str,
    bucket: str,
) -> str:
    raw = f"{business_id}|{alert_type}|{title.strip()}|{message.strip()}|{bucket}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _create_alert_if_new(
    db: AsyncSession,
    *,
    business_id,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    dedupe_bucket: str,
):
    dedupe_key = _alert_dedupe_key(
        business_id=business_id,
        alert_type=alert_type,
        title=title,
        message=message,
        bucket=dedupe_bucket,
    )
    try:
        async with db.begin_nested():
            alert = Alert(
                business_id=business_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                dedupe_key=dedupe_key,
            )
            db.add(alert)
            await db.flush()
            return alert
    except IntegrityError:
        return None


# ── Background pipeline executor ──────────────────────────────────────────────

async def _run_pipeline_background(
    run_id: uuid.UUID,
    content: bytes,
    file_type: str,
    triggered_by: str,
    ws_manager,
):
    """
    Executes the full LangGraph pipeline in the background.
    Updates the PipelineRun record in DB when done.
    Pushes WebSocket events throughout (each node calls push_agent_event).
    """
    import logging
    logger = logging.getLogger("pipeline_runner")

    graph = build_graph(AsyncSessionLocal, ws_manager)

    initial_state: FinAgentState = {
        "run_id": str(run_id),
        "triggered_by": triggered_by,
        "file_content": content,
        "file_type": file_type,
        "errors": [],
        "completed_agents": [],
        "status": "running",
        "_ws_manager": ws_manager,
    }

    try:
        final_state = await graph.ainvoke(initial_state)
        final_status = RunStatus.completed if final_state.get("status") == "completed" else RunStatus.failed
        error_msg = str(final_state.get("errors", [])) if final_state.get("errors") else None
        summary = str(final_state.get("completed_agents", []))
    except Exception as exc:
        logger.error("[PipelineRunner] Unhandled exception for run_id=%s: %s", run_id, exc)
        final_status = RunStatus.failed
        error_msg = str(exc)
        summary = "pipeline_crashed"

    # Persist final status to DB
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = final_status
                run.completed_at = datetime.now(timezone.utc)
                run.summary = summary
                run.error_message = error_msg
                await db.commit()
    except Exception as db_exc:
        logger.error("[PipelineRunner] Failed to update pipeline run status: %s", db_exc)

    logger.info(
        "[PipelineRunner] run_id=%s finished with status=%s",
        run_id, final_status
    )


# ── Pipeline trigger ──────────────────────────────────────────────────────────

@router.post("/run", status_code=202, dependencies=[Depends(verify_api_key)])
@limiter.limit("3/minute")
async def trigger_pipeline(
    request: Request,
    file: UploadFile = File(...),
    file_type: str = Form("csv"),
    triggered_by: str = Form("manual"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV/JSON file and trigger the full agent pipeline.
    Returns 202 Accepted immediately with a run_id.
    Pipeline runs in the background — poll /runs/{run_id}/status or
    listen on the WebSocket for live progress events.

    Deduplication: if the same file (SHA-256 hash) has already been successfully
    processed, returns the existing run_id instead of re-running the pipeline.
    """
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > 10 * 1024 * 1024:  # 10 MB guard
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    # ── SHA-256 deduplication ─────────────────────────────────────────────────
    data_hash = hashlib.sha256(content).hexdigest()
    existing = await db.execute(
        select(PipelineRun)
        .where(PipelineRun.data_hash == data_hash)
        .where(PipelineRun.status == RunStatus.completed)
        .order_by(PipelineRun.started_at.desc())
        .limit(1)
    )
    existing_run = existing.scalar_one_or_none()
    if existing_run:
        return {
            "run_id": str(existing_run.id),
            "status": "duplicate",
            "message": "This file has already been processed. Returning the existing run.",
        }
    # ─────────────────────────────────────────────────────────────────────────

    run_id = uuid.uuid4()

    # Create DB record immediately so status polling works right away
    pipeline_run = PipelineRun(
        id=run_id,
        triggered_by=triggered_by,
        status=RunStatus.running,
        data_hash=data_hash,
    )
    db.add(pipeline_run)
    await db.commit()

    ws_manager = getattr(request.app.state, "ws_manager", None)

    # Fire-and-forget background task — does NOT block the HTTP response
    asyncio.create_task(
        _run_pipeline_background(run_id, content, file_type, triggered_by, ws_manager)
    )

    return {
        "run_id": str(run_id),
        "status": "accepted",
        "message": "Pipeline started. Poll /api/v1/runs/{run_id}/status or watch the WebSocket for live updates.",
    }


# ── Run status polling ────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/status")
async def get_run_status(run_id: str, db: AsyncSession = Depends(get_db)):
    """Poll this endpoint to check if a pipeline run has completed."""
    try:
        uid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format")

    result = await db.execute(select(PipelineRun).where(PipelineRun.id == uid))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": str(run.id),
        "status": run.status,
        "triggered_by": run.triggered_by,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "summary": run.summary,
        "error_message": run.error_message,
    }


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FinancialReport).order_by(FinancialReport.created_at.desc()).limit(20)
    )
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "run_id": str(r.run_id),
            "period_start": r.period_start,
            "period_end": r.period_end,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.get("/reports/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FinancialReport).where(FinancialReport.id == uuid.UUID(report_id))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": str(report.id),
        "pnl_data": report.pnl_data,
        "forecast_data": report.forecast_data,
        "anomalies": report.anomalies,
        "reconciliation": report.reconciliation,
        "executive_summary": report.executive_summary,
        "markdown_report": report.markdown_report,
        "created_at": report.created_at,
    }


# ── Audit logs ────────────────────────────────────────────────────────────────

@router.get("/audit/{run_id}")
async def get_audit_trail(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.run_id == uuid.UUID(run_id))
        .order_by(AuditLog.created_at)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "agent_name": l.agent_name,
            "action": l.action,
            "tokens_used": l.tokens_used,
            "duration_ms": l.duration_ms,
            "status": l.status,
            "created_at": l.created_at,
        }
        for l in logs
    ]


# ── Pipeline runs list ────────────────────────────────────────────────────────

@router.get("/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(50)
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "triggered_by": r.triggered_by,
            "status": r.status,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
        }
        for r in runs
    ]


# ── Settings info & Data Management ───────────────────────────────────────────

@router.delete("/data/reset", dependencies=[Depends(verify_api_key)])
async def reset_data(db: AsyncSession = Depends(get_db)):
    """
    Hard delete all financial data, analysis runs, alerts, and chat history.
    Resets the business profile back to a clean state.
    """
    from sqlalchemy import delete
    from db.models import (
        Transaction, PipelineRun, FinancialReport, Anomaly, CategoryBaseline,
        Alert, ChatMessage, AuditLog, BusinessProfile
    )
    from services.profile_service import get_or_create_profile
    from db.redis_client import get_redis
    
    profile = await get_or_create_profile(db)
    business_id = profile.id
    
    # We must delete in an order that respects foreign keys (if any are enforced).
    # Currently, models have business_id or run_id.
    
    # 1. Delete items linked to BusinessProfile directly
    await db.execute(delete(Transaction).where(Transaction.business_id == business_id))
    await db.execute(delete(CategoryBaseline).where(CategoryBaseline.business_id == business_id))
    await db.execute(delete(Alert).where(Alert.business_id == business_id))
    await db.execute(delete(ChatMessage).where(ChatMessage.business_id == business_id))
    
    # 2. Since this is single-tenant MVP, we can safely delete all runs, reports, anomalies, and audits
    # Alternatively, find all runs for the business. Since MVP is single-tenant, let's just clear the tables.
    await db.execute(delete(Anomaly))
    await db.execute(delete(FinancialReport))
    await db.execute(delete(AuditLog))
    await db.execute(delete(PipelineRun))
    
    # 3. Reset the BusinessProfile stats
    profile.total_uploads = 0
    profile.first_data_date = None
    profile.latest_data_date = None
    profile.health_score = 50.0
    profile.health_score_history = []
    profile.avg_monthly_revenue = 0.0
    profile.avg_monthly_expenses = 0.0
    profile.avg_monthly_burn = 0.0
    
    await db.commit()
    
    # 4. Clear Redis chat memory
    try:
        redis = await get_redis()
        # Delete all chat:* keys
        keys = await redis.keys("chat:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        import logging
        logging.getLogger("routes").warning(f"Failed to clear Redis keys: {e}")
            
    return {"status": "success", "message": "All financial data has been completely reset."}


@router.get("/settings")
async def get_settings():
    """Returns current provider configuration and settings (read-only)."""
    import os
    return {
        "tax_rate_pct": float(os.getenv("TAX_RATE_PCT", "25")),
        "providers": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        },
        "active_groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "active_anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    }


# ── Chat Agent (Phase 4) ──────────────────────────────────────────────────────

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # if None, a new session is created


@router.post("/chat", dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the CashPilot ReAct chat agent.

    The agent automatically selects and calls financial tools (compute_pnl,
    compute_runway, find_anomalies, etc.) to ground its answers in real data.

    Body:
        message    — the user's question
        session_id — optional; omit to start a new conversation

    Returns:
        response   — agent's answer (data-grounded)
        tools_used — list of tool names invoked in this turn
        session_id — use this in subsequent requests to maintain context
    """
    import logging
    log = logging.getLogger("chat_endpoint")

    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty")

    session_id = body.session_id or str(uuid.uuid4())

    # Get the single-tenant business profile
    try:
        from services.profile_service import get_or_create_profile
        profile = await get_or_create_profile(db)
        business_id = profile.id
    except Exception as exc:
        log.warning("[Chat] Could not load business profile: %s", exc)
        business_id = None

    try:
        from agents.chat_agent import run_chat
        result = await run_chat(
            message=message,
            session_id=session_id,
            db=db,
            business_id=business_id,
        )
        # If the agent returned an error field, include it in the response
        # so the frontend can display it in dev mode
        return result
    except Exception as exc:
        log.error("[Chat] Agent failed: %s", exc)
        import traceback
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Chat agent error: {str(exc)}",
                "traceback": traceback.format_exc(),
            }
        )


@router.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    """
    Return the conversation history for a session (from Redis).
    Messages are returned in chronological order.
    """
    from db.redis_client import load_chat_history
    messages = await load_chat_history(session_id, max_messages=100)
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": msg.__class__.__name__.replace("Message", "").lower(),
                "content": msg.content,
            }
            for msg in messages
        ],
        "count": len(messages),
    }


@router.delete("/chat/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear conversation history for a session (from Redis only; DB records kept)."""
    from db.redis_client import clear_chat_history
    await clear_chat_history(session_id)
    return {"session_id": session_id, "cleared": True}


# ── Watch Engine (Phase 6) ────────────────────────────────────────────────────

@router.get("/alerts")
async def list_alerts(db: AsyncSession = Depends(get_db)):
    """Get all alerts, newest first."""
    result = await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(50))
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "is_read": a.is_read,
            "created_at": a.created_at,
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an alert as read."""
    try:
        uid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert_id format")

    result = await db.execute(select(Alert).where(Alert.id == uid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    await db.commit()
    return {"status": "success", "alert_id": alert_id}


@router.delete("/alerts/{alert_id}")
async def dismiss_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Dismiss (permanently delete) an alert."""
    try:
        uid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert_id format")

    result = await db.execute(select(Alert).where(Alert.id == uid))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()
    return {"status": "dismissed", "alert_id": alert_id}


# ── Snapshot Dashboard (Phase 2A) ─────────────────────────────────────────────

@router.get("/snapshot")
async def get_snapshot(db: AsyncSession = Depends(get_db)):
    """
    Aggregated financial dashboard data for the Snapshot page.

    Data-aware: anchors all period calculations to the actual date range of
    the uploaded transactions, not to today's date. This means data from 2023
    will show 2023 numbers correctly instead of zeros.
    """
    import logging
    from collections import defaultdict
    from datetime import datetime, timezone
    from dateutil.relativedelta import relativedelta
    from sqlalchemy import func as sqlfunc
    from services.profile_service import get_or_create_profile
    from tools.financial_tools import compute_pnl, compute_runway, find_anomalies
    from db.models import Transaction as TxModel

    log = logging.getLogger("snapshot_endpoint")

    try:
        profile = await get_or_create_profile(db)
        business_id = profile.id
    except Exception as exc:
        log.error("[Snapshot] Could not load business profile: %s", exc)
        raise HTTPException(status_code=500, detail="Could not load business profile")

    # ── Detect actual data date range ─────────────────────────────────────────
    try:
        date_result = await db.execute(
            select(
                sqlfunc.min(TxModel.date).label("min_date"),
                sqlfunc.max(TxModel.date).label("max_date"),
            ).where(TxModel.business_id == business_id)
        )
        date_row = date_result.one_or_none()
        data_min = date_row.min_date if date_row else None
        data_max = date_row.max_date if date_row else None
    except Exception as exc:
        log.warning("[Snapshot] Could not determine data date range: %s", exc)
        data_min = data_max = None

    has_data = data_min is not None and data_max is not None

    # ── Determine the "current" and "previous" month anchored to data ─────────
    # Use the last month that has data as "current", the month before as "previous"
    if has_data:
        # Ensure timezone-aware
        if data_max.tzinfo is None:
            data_max_tz = data_max.replace(tzinfo=timezone.utc)
        else:
            data_max_tz = data_max

        # "Current" period = the calendar month of the latest data point
        curr_month_start = data_max_tz.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        curr_month_end = (curr_month_start + relativedelta(months=1)) - relativedelta(seconds=1)

        # "Previous" period = the calendar month before that
        prev_month_end = curr_month_start - relativedelta(seconds=1)
        prev_month_start = prev_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        period_current = f"{curr_month_start.date()}:{curr_month_end.date()}"
        period_previous = f"{prev_month_start.date()}:{prev_month_end.date()}"

        # For runway: use last 90 days of data relative to data_max
        if data_min.tzinfo is None:
            data_min_tz = data_min.replace(tzinfo=timezone.utc)
        else:
            data_min_tz = data_min
    else:
        period_current = "this_month"
        period_previous = "last_month"

    # ── PnL for current vs previous period ───────────────────────────────────
    try:
        pnl_this = await compute_pnl(db, business_id, period=period_current)
        pnl_last = await compute_pnl(db, business_id, period=period_previous)
    except Exception as exc:
        log.error("[Snapshot] PnL computation failed: %s", exc)
        pnl_this = {"revenue": 0, "expenses": 0, "gross_profit": 0, "margin_pct": 0}
        pnl_last = {"revenue": 0, "expenses": 0, "gross_profit": 0, "margin_pct": 0}

    # ── Runway — data-aware ───────────────────────────────────────────────────
    try:
        runway = await compute_runway(db, business_id)
    except Exception as exc:
        log.warning("[Snapshot] Runway computation failed: %s", exc)
        runway = {"months_of_runway": None, "net_burn": 0}

    def _trend_direction(change: float) -> str:
        if change > 0.5:
            return "positive"
        if change < -0.5:
            return "negative"
        return "neutral"

    def _pct_change(current: float, previous: float) -> float:
        if previous == 0:
            return 0.0
        return round((current - previous) / abs(previous) * 100, 1)

    rev_trend = _pct_change(pnl_this["revenue"], pnl_last["revenue"])
    exp_trend = _pct_change(pnl_this["expenses"], pnl_last["expenses"])
    margin_trend = round(pnl_this["margin_pct"] - pnl_last["margin_pct"], 2)
    runway_months = runway.get("months_of_runway") or 0

    # ── Chart data: 12 months anchored to data range ──────────────────────────
    try:
        monthly: dict[str, dict] = defaultdict(lambda: {"revenue": 0.0, "expenses": 0.0})

        if has_data:
            # Anchor chart to the last month of data, go back 12 months
            anchor = data_max_tz.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            anchor = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for i in range(11, -1, -1):
            m_start = anchor - relativedelta(months=i)
            m_end = (m_start + relativedelta(months=1)) - relativedelta(seconds=1)
            period_label = m_start.strftime("%Y-%m")
            m_pnl = await compute_pnl(
                db, business_id,
                period=f"{m_start.date()}:{m_end.date()}"
            )
            monthly[period_label]["revenue"] = m_pnl.get("revenue", 0)
            monthly[period_label]["expenses"] = m_pnl.get("expenses", 0)

        chart_data = [
            {"date": f"{k}-01", "revenue": v["revenue"], "expenses": v["expenses"]}
            for k, v in sorted(monthly.items())
        ]
    except Exception as exc:
        log.warning("[Snapshot] Chart data computation failed (non-fatal): %s", exc)
        chart_data = []

    # ── Sparklines ────────────────────────────────────────────────────────────
    sparkline = [{"date": d["date"], "value": d["revenue"]} for d in chart_data[-7:]]
    exp_sparkline = [{"date": d["date"], "value": d["expenses"]} for d in chart_data[-7:]]
    margin_sparkline = [
        {
            "date": d["date"],
            "value": round((d["revenue"] - d["expenses"]) / d["revenue"] * 100, 1)
            if d["revenue"] > 0 else 0,
        }
        for d in chart_data[-7:]
    ]

    # ── Anomalies — anchored to data range ────────────────────────────────────
    try:
        if has_data:
            # Use the last 30 days of actual data
            anomaly_end = data_max_tz
            anomaly_start = anomaly_end - relativedelta(days=30)
            anomaly_period = f"{anomaly_start.date()}:{anomaly_end.date()}"
        else:
            anomaly_period = "last_30d"

        anomaly_res = await find_anomalies(db, business_id, period=anomaly_period)
        raw_anomalies = anomaly_res.get("anomalies", [])
        anomalies = [
            {
                "id": a.get("id", str(uuid.uuid4())),
                "title": f"Anomalous {a.get('category', 'transaction').title()} — ${abs(a.get('amount', 0)):,.2f}",
                "severity": "critical" if a.get("z_score", 0) > 3.5 else "warning" if a.get("z_score", 0) > 2.5 else "info",
                "date": a.get("date"),
            }
            for a in raw_anomalies[:5]
        ]
    except Exception as exc:
        log.warning("[Snapshot] Anomaly detection failed (non-fatal): %s", exc)
        anomalies = []

    # ── Last synced timestamp ─────────────────────────────────────────────────
    last_synced = None
    if profile.latest_data_date:
        last_synced = profile.latest_data_date.isoformat()
    elif has_data and data_max:
        last_synced = data_max.isoformat()

    return {
        "quickStats": {
            "totalRevenue": {
                "value": pnl_this["revenue"],
                "trend": rev_trend,
                "trendDirection": _trend_direction(rev_trend),
                "sparkline": sparkline,
            },
            "totalExpenses": {
                "value": pnl_this["expenses"],
                "trend": exp_trend,
                "trendDirection": _trend_direction(-exp_trend),
                "sparkline": exp_sparkline,
            },
            "netProfitMargin": {
                "value": pnl_this["margin_pct"],
                "trend": margin_trend,
                "trendDirection": _trend_direction(margin_trend),
                "sparkline": margin_sparkline,
            },
            "cashRunway": {
                "value": runway_months,
                "trend": 0,
                "trendDirection": "neutral" if runway_months >= 6 else "negative",
                "sparkline": [],
            },
        },
        "chartData": chart_data,
        "healthScore": profile.health_score or 50.0,
        "anomalies": anomalies,
        "lastSyncedAt": last_synced,
    }


# ── History — Pipeline runs list with report context (Phase 2B) ───────────────

@router.get("/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    """
    Returns a list of completed pipeline runs with summary and report metadata.
    Used by the History page to display the analysis timeline.
    """
    result = await db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(50)
    )
    runs = result.scalars().all()

    # Fetch linked reports for each completed run
    run_ids = [r.id for r in runs if r.status == RunStatus.completed]
    report_map: dict = {}
    if run_ids:
        reports_result = await db.execute(
            select(FinancialReport).where(FinancialReport.run_id.in_(run_ids))
        )
        for r in reports_result.scalars().all():
            report_map[str(r.run_id)] = {
                "report_id": str(r.id),
                "executive_summary": (r.executive_summary or "")[:300],
                "period_start": r.period_start,
                "period_end": r.period_end,
            }

    return [
        {
            "run_id": str(r.id),
            "status": r.status,
            "triggered_by": r.triggered_by,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "summary": r.summary,
            "report": report_map.get(str(r.id)),
        }
        for r in runs
    ]


@router.post("/internal/nightly-delta", dependencies=[Depends(verify_internal_secret)])
async def nightly_delta_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Internal endpoint called by Celery nightly_delta_check task.
    Computes current runway, anomaly detection, margin trends, and generates Alerts.
    """
    import logging
    log = logging.getLogger("watch_engine.nightly")
    from services.profile_service import get_or_create_profile
    from tools.financial_tools import compute_runway, find_anomalies, compare_periods

    profile = await get_or_create_profile(db)
    business_id = profile.id
    ws_manager = getattr(request.app.state, "ws_manager", None)
    alerts_created = []

    # 1. Compute runway
    runway_res = await compute_runway(db, business_id)
    warning = runway_res.get("warning")
    today_bucket = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if warning:
        runway_months = runway_res.get("months_of_runway")
        alert = await _create_alert_if_new(
            db,
            business_id=business_id,
            alert_type="runway_warning",
            severity="critical" if (runway_months is not None and runway_months < 3) else "high",
            title="Low Runway Alert",
            message=warning,
            dedupe_bucket=today_bucket,
        )
        if alert:
            alerts_created.append(alert)

    # 2. Check each category against EWMA baseline via find_anomalies
    anomalies_res = await find_anomalies(db, business_id, period="last_30d", use_baselines=True, z_threshold=2.0)
    if anomalies_res.get("total_flagged", 0) > 0:
        for anomaly in anomalies_res.get("anomalies", []):
            if anomaly.get("z_score", 0) > 2.5: # Only alert for significant anomalies
                alert = await _create_alert_if_new(
                    db,
                    business_id=business_id,
                    alert_type="category_spike",
                    severity="high" if anomaly.get("z_score", 0) > 3.0 else "medium",
                    title=f"Spending Spike: {anomaly.get('category', 'unknown').title()}",
                    message=f"Anomalous transaction of {anomaly.get('amount')} detected in {anomaly.get('category', 'unknown')} on {anomaly.get('date')}.",
                    dedupe_bucket=today_bucket,
                )
                if alert:
                    alerts_created.append(alert)
                # Cap the number of individual alerts to avoid spam
                if len(alerts_created) > 5:
                    break

    # 3. Check margin trend 
    # (A simple check for this month vs last month)
    margin_res = await compare_periods(db, business_id, period_a="this_month", period_b="last_month", metric="margin_pct")
    if margin_res.get("change_abs") is not None and margin_res.get("change_abs") < -5.0:
        alert = await _create_alert_if_new(
            db,
            business_id=business_id,
            alert_type="margin_trend",
            severity="high",
            title="Margin Decline Alert",
            message=f"Gross margin has decreased by {abs(margin_res['change_abs']):.1f}% compared to last month.",
            dedupe_bucket=today_bucket,
        )
        if alert:
            alerts_created.append(alert)

    if alerts_created:
        await db.commit()
        if ws_manager:
            for a in alerts_created:
                payload = {
                    "id": str(a.id),
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "title": a.title,
                    "message": a.message,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                await ws_manager.broadcast({"type": "alert", "data": payload})

    log.info("[WatchEngine] Nightly delta check completed. Generated %d alerts.", len(alerts_created))
    return {"status": "success", "alerts_generated": len(alerts_created)}


@router.post("/internal/weekly-digest", dependencies=[Depends(verify_internal_secret)])
async def weekly_digest_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Internal endpoint called by Celery weekly_digest task.
    Uses LLM to summarize the week's changes and saves as an Alert.
    """
    import logging
    log = logging.getLogger("watch_engine.weekly")
    from services.profile_service import get_or_create_profile
    from tools.financial_tools import compare_periods
    from tools.llm_with_tools import get_llm_with_tools
    from langchain_core.messages import SystemMessage, HumanMessage

    profile = await get_or_create_profile(db)
    business_id = profile.id
    ws_manager = getattr(request.app.state, "ws_manager", None)

    from datetime import datetime, timedelta, timezone
    today = datetime.now(timezone.utc).date()
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    
    period_a = f"{this_week_start}:{this_week_start + timedelta(days=6)}"
    period_b = f"{last_week_start}:{last_week_start + timedelta(days=6)}"

    # Gather data for the prompt
    rev_comp = await compare_periods(db, business_id, period_a=period_a, period_b=period_b, metric="revenue")
    exp_comp = await compare_periods(db, business_id, period_a=period_a, period_b=period_b, metric="expenses")
    margin_comp = await compare_periods(db, business_id, period_a=period_a, period_b=period_b, metric="margin_pct")

    context = f"""
    Compare this week's metrics to last week.
    Revenue: {rev_comp.get('interpretation')}
    Expenses: {exp_comp.get('interpretation')}
    Margin: {margin_comp.get('interpretation')}
    """

    system_prompt = """You are CashPilot. Write a concise, 3-5 sentence executive summary of this week's financial changes based on the provided metrics. Keep it professional and action-oriented."""
    
    try:
        # We don't need tools for just summarizing
        llm = get_llm_with_tools([])
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=context)]
        response = await llm.ainvoke(messages)
        summary = response.content
    except Exception as e:
        log.error("Failed to generate weekly digest with LLM: %s", e)
        summary = f"Weekly summary could not be generated. Data: {rev_comp.get('interpretation')} {exp_comp.get('interpretation')}"

    week_bucket = f"{this_week_start.isoformat()}:{(this_week_start + timedelta(days=6)).isoformat()}"
    alert = await _create_alert_if_new(
        db,
        business_id=business_id,
        alert_type="digest",
        severity="low",
        title="Weekly Financial Digest",
        message=summary,
        dedupe_bucket=week_bucket,
    )
    if not alert:
        return {"status": "success", "alert_id": None, "deduped": True}
    await db.commit()

    if ws_manager:
        payload = {
            "id": str(alert.id),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        await ws_manager.broadcast({"type": "alert", "data": payload})

    log.info("[WatchEngine] Weekly digest generated.")
    return {"status": "success", "alert_id": str(alert.id)}

