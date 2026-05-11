"""
FastAPI routes — public API surface for the LedgerMind platform.
POST /run returns 202 immediately; pipeline runs as a background asyncio task.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AuditLog, FinancialReport, PipelineRun, RunStatus, get_db, AsyncSessionLocal
from graph.workflow import FinAgentState, build_graph
from api.auth import verify_api_key

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


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
    """
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > 10 * 1024 * 1024:  # 10 MB guard
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    run_id = uuid.uuid4()

    # Create DB record immediately so status polling works right away
    pipeline_run = PipelineRun(
        id=run_id,
        triggered_by=triggered_by,
        status=RunStatus.running,
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


# ── Settings info (read-only) ─────────────────────────────────────────────────

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
