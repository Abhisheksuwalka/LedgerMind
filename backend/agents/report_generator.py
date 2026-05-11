"""
Agent 7 — Report Generator
Compiles outputs from all analysis agents into a boardroom-ready financial report.
Uses LLM router with prefer_provider="anthropic" for highest quality,
but gracefully falls back to Groq/Gemini if Anthropic is not configured.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from tools.llm_router import run_agent

logger = logging.getLogger("agent.report_generator")

SYSTEM_PROMPT = """You are the CFO-level reporting AI for LedgerMind.

You have received outputs from all analysis agents. Your task is to compile a boardroom-ready financial report.

Write:
1. Executive Summary (3-4 paragraphs) — plain English, no jargon, suitable for a non-financial executive.
2. Key Metrics section — a concise table of the 5 most important numbers.
3. Top 3 Risks identified this period with severity and recommended action.
4. Top 3 Opportunities for cost reduction or revenue growth.
5. Recommended Next Actions (numbered list, 5 items max).

Format your entire response as a Markdown document starting with:
# LedgerMind — Financial Report"""


async def generate_report(state: dict) -> dict:
    run_id = state.get("run_id")
    logger.info("[ReportGenerator] Compiling report for run_id=%s", run_id)

    pnl = state.get("pnl_result", {})
    forecast = state.get("forecast_result", {})
    anomaly = state.get("anomaly_result", {})
    reconciliation = state.get("reconciliation_result", {})

    context = {
        "run_id": run_id,
        "report_date": datetime.now(timezone.utc).isoformat(),
        "pnl_summary": {
            "revenue": pnl.get("revenue"),
            "expenses": pnl.get("expenses"),
            "gross_profit": pnl.get("gross_profit"),
            "net_profit": pnl.get("net_profit"),
            "gross_margin_pct": pnl.get("gross_margin_pct"),
            "health_score": pnl.get("health_score"),
            "key_insights": pnl.get("key_insights", []),
            "alerts": pnl.get("alerts", []),
        },
        "forecast_summary": {
            "30_day_projection": forecast.get("projections", {}).get(30),
            "60_day_projection": forecast.get("projections", {}).get(60),
            "90_day_projection": forecast.get("projections", {}).get(90),
            "confidence": forecast.get("confidence_level"),
            "risk_factors": forecast.get("risk_factors", []),
            "narrative": forecast.get("narrative_summary", ""),
        },
        "anomaly_summary": {
            "total_flagged": anomaly.get("total_flagged", 0),
            "critical_count": anomaly.get("critical_count", 0),
            "top_anomalies": (anomaly.get("anomalies") or [])[:3],
        },
        "reconciliation_summary": {
            "match_rate_pct": reconciliation.get("match_rate_pct"),
            "discrepancy_count": reconciliation.get("discrepancy_count", 0),
            "risk_level": reconciliation.get("risk_level"),
            "action_plan": reconciliation.get("action_plan", []),
        },
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
                pnl_data=pnl,
                forecast_data=forecast,
                anomalies=anomaly.get("anomalies", []),
                reconciliation=reconciliation,
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
        "tokens_used": llm_result["tokens_used"],
        "llm_provider": provider_used,
    }
