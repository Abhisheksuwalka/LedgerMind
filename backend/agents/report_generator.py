"""
Agent 7 — Report Generator (Phase 5 Redesign)
Compiles findings from the ReAct Analysis Agent into a boardroom-ready financial report.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from tools.llm_router import run_agent

logger = logging.getLogger("agent.report_generator")

SYSTEM_PROMPT = """You are the CFO-level reporting AI for CashPilot.

You have received findings from the Analysis Agent. Your task is to compile a boardroom-ready financial report.

Write:
1. Executive Summary (3-4 paragraphs) — plain English, no jargon, suitable for a non-financial executive.
2. Key Insights section — based directly on the provided findings.
3. Top Risks/Anomalies (if any are mentioned in the findings).
4. Recommended Next Actions.

Format your entire response as a Markdown document starting with:
# CashPilot — Financial Report"""


async def generate_report(state: dict) -> dict:
    run_id = state.get("run_id")
    logger.info("[ReportGenerator] Compiling report for run_id=%s", run_id)

    findings = state.get("analysis_findings", [])
    if not findings:
        findings = ["No specific findings were generated for this period."]

    context = {
        "run_id": run_id,
        "report_date": datetime.now(timezone.utc).isoformat(),
        "analysis_findings": findings,
    }

    # Prefer Anthropic for report quality — falls back to Groq/Gemini automatically
    llm_result = await run_agent(
        system_prompt=SYSTEM_PROMPT,
        context=context,
        max_tokens=3000,
        use_cache=False,          # always generate a fresh report
        prefer_provider="anthropic",
    )

    markdown_report = llm_result["text"]
    provider_used = llm_result.get("provider", "unknown")
    logger.info(
        "[ReportGenerator] Report generated — %d chars, provider=%s, %dms",
        len(markdown_report), provider_used, llm_result.get("duration_ms", 0),
    )

    # Persist to DB
    report_id: Optional[str] = None
    try:
        from db.models import AsyncSessionLocal, FinancialReport

        async with AsyncSessionLocal() as db:
            report_row = FinancialReport(
                run_id=uuid.UUID(run_id) if run_id else None,
                # We store the structured findings in one of the existing JSON columns
                # so we don't have to run an Alembic migration right now.
                pnl_data={"findings": findings},
                forecast_data={},
                anomalies=[],
                reconciliation={},
                markdown_report=markdown_report,
                executive_summary=markdown_report[:2000],
            )
            db.add(report_row)
            await db.commit()
            report_id = str(report_row.id)
    except Exception as exc:
        logger.warning("[ReportGenerator] DB persist failed: %s", exc)

    return {
        "report_id": report_id,
        "markdown_report": markdown_report,
        "executive_summary": markdown_report[:2000],
        "findings": findings,
        "tokens_used": llm_result["tokens_used"],
        "llm_provider": provider_used,
    }
