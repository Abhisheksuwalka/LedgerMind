"""
LangGraph state machine — orchestrates all agents.
Each node receives and mutates the shared FinAgentState TypedDict.

Phase 5 changes:
  - Replaced fixed parallel analysis agents with a single dynamic ReAct Analysis Agent.
"""

import logging
import operator
import time
from typing import Annotated, Any, Optional
from uuid import UUID

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

logger = logging.getLogger("workflow")


# ── Shared state ──────────────────────────────────────────────────────────────

class FinAgentState(TypedDict, total=False):
    run_id: str
    triggered_by: str
    file_content: bytes
    file_type: str
    business_id: str

    # agent outputs
    ingestion_result: dict
    analysis_findings: list[str]
    report_result: dict

    # control (using Annotated to merge parallel updates)
    errors: Annotated[list[dict], operator.add]
    completed_agents: Annotated[list[str], operator.add]
    status: str  # running | completed | failed
    _ws_manager: Any


# ── Audit helper ──────────────────────────────────────────────────────────────

async def _audit(
    db_session_factory,
    run_id: Optional[str],
    agent_name: str,
    action: str,
    status: str,
    duration_ms: int,
    tokens_used: int = 0,
    llm_provider: Optional[str] = None,
    output_data: Optional[dict] = None,
    error: Optional[str] = None,
):
    """Fire-and-forget audit log — errors are swallowed so they never crash a node."""
    try:
        from agents.audit import log_agent_action
        async with db_session_factory() as db:
            await log_agent_action(
                run_id=run_id,
                agent_name=agent_name,
                action=action,
                input_data=None,
                output_data=output_data,
                llm_provider=llm_provider,
                tokens_used=tokens_used,
                duration_ms=duration_ms,
                status=status,
                error=error,
                db=db,
            )
    except Exception as exc:
        logger.warning("[Audit] Failed to write audit entry for %s: %s", agent_name, exc)


# ── Node implementations ──────────────────────────────────────────────────────

def make_ingestion_node(db_session_factory, run_id_getter):
    from agents.data_ingestion import ingest
    from agents.dashboard_agent import push_agent_event
    from services.baseline_updater import update_baselines_for_run
    from services.profile_service import get_or_create_profile, update_profile_after_run

    async def ingestion(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        run_id = state.get("run_id")
        await push_agent_event("agent_started", "data_ingestion", {}, ws)
        t0 = time.monotonic()
        try:
            # Get or create business profile first
            async with db_session_factory() as db:
                profile = await get_or_create_profile(db)
                business_id = profile.id

            async with db_session_factory() as db:
                result = await ingest(
                    content=state["file_content"],
                    file_type=state.get("file_type", "csv"),
                    run_id=state.get("run_id"),
                    business_id=business_id,
                    db=db,
                )

            # ── Phase 2: update business profile + baselines ─────────────────
            try:
                async with db_session_factory() as db:
                    # Update EWMA category baselines
                    await update_baselines_for_run(
                        db=db,
                        business_id=business_id,
                        transactions=result.get("transactions", []),
                    )

                    # Update profile stats (PnL not available yet)
                    await update_profile_after_run(
                        db=db,
                        business_id=business_id,
                        ingestion_result=result,
                        pnl_result=None,
                    )

                result["business_id"] = str(business_id)
            except Exception as bex:
                logger.warning("[DataIngestion] Baseline/profile update failed (non-fatal): %s", bex)
                business_id = None
            # ─────────────────────────────────────────────────────────────────

            duration_ms = int((time.monotonic() - t0) * 1000)
            await push_agent_event("agent_done", "data_ingestion",
                                   {"total_transactions": result.get("total_transactions")}, ws)
            await _audit(db_session_factory, run_id, "data_ingestion", "ingest",
                         "success", duration_ms,
                         output_data={"total_transactions": result.get("total_transactions")})
            
            updates = {"ingestion_result": result, "completed_agents": ["data_ingestion"]}
            if business_id:
                updates["business_id"] = str(business_id)
            return updates
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.error("[DataIngestion] failed: %s", exc)
            await push_agent_event("agent_error", "data_ingestion", {"error": str(exc)}, ws)
            await _audit(db_session_factory, run_id, "data_ingestion", "ingest",
                         "error", duration_ms, error=str(exc))
            return {"errors": [{"agent": "data_ingestion", "error": str(exc)}], "status": "failed"}

    return ingestion


def make_analysis_node(db_session_factory):
    from agents.analysis_agent import run_analysis
    from agents.dashboard_agent import push_agent_event

    async def analysis(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        run_id = state.get("run_id")
        business_id = state.get("business_id")
        if not business_id:
            logger.warning("[AnalysisAgent] No business_id, skipping.")
            return {"analysis_findings": ["No business profile available to analyze."]}

        await push_agent_event("agent_started", "analysis_agent", {}, ws)
        t0 = time.monotonic()
        try:
            async with db_session_factory() as db:
                findings = await run_analysis(db, business_id)

            duration_ms = int((time.monotonic() - t0) * 1000)
            await push_agent_event("agent_done", "analysis_agent",
                                   {"findings_count": len(findings)}, ws)
            await _audit(db_session_factory, run_id, "analysis_agent", "analyze",
                         "success", duration_ms,
                         output_data={"findings_count": len(findings)})
            return {"analysis_findings": findings, "completed_agents": ["analysis_agent"]}
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.error("[AnalysisAgent] failed: %s", exc)
            await push_agent_event("agent_error", "analysis_agent", {"error": str(exc)}, ws)
            await _audit(db_session_factory, run_id, "analysis_agent", "analyze",
                         "error", duration_ms, error=str(exc))
            return {"errors": [{"agent": "analysis_agent", "error": str(exc)}]}

    return analysis


def make_report_node(db_session_factory):
    from agents.report_generator import generate_report
    from agents.dashboard_agent import push_agent_event

    async def report(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        run_id = state.get("run_id")
        await push_agent_event("agent_started", "report_generator", {}, ws)
        t0 = time.monotonic()
        try:
            result = await generate_report(state)
            duration_ms = int((time.monotonic() - t0) * 1000)
            await push_agent_event("agent_done", "report_generator",
                                   {"report_id": result.get("report_id")}, ws)
            await _audit(db_session_factory, run_id, "report_generator", "generate",
                         "success", duration_ms,
                         tokens_used=result.get("tokens_used", 0),
                         llm_provider=result.get("llm_provider"),
                         output_data={"report_id": result.get("report_id")})
            return {"report_result": result, "completed_agents": ["report_generator"], "status": "completed"}
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            logger.error("[ReportGenerator] failed: %s", exc)
            await push_agent_event("agent_error", "report_generator", {"error": str(exc)}, ws)
            await _audit(db_session_factory, run_id, "report_generator", "generate",
                         "error", duration_ms, error=str(exc))
            return {"errors": [{"agent": "report_generator", "error": str(exc)}], "status": "failed"}

    return report


def make_notification_node():
    from agents.notification import send_notifications

    async def notification(state: FinAgentState) -> dict:
        try:
            await send_notifications(state)
            return {"completed_agents": ["notification"]}
        except Exception as exc:
            logger.error("[Notification] failed: %s", exc)
            return {"errors": [{"agent": "notification", "error": str(exc)}]}

    return notification


def make_audit_node(db_session_factory):
    from agents.audit import log_run

    async def audit(state: FinAgentState) -> dict:
        try:
            async with db_session_factory() as db:
                await log_run(state, db)
            return {"completed_agents": ["audit"]}
        except Exception as exc:
            logger.error("[Audit] failed: %s", exc)
            return {}

    return audit


def make_dashboard_node(ws_manager):
    from agents.dashboard_agent import push_update

    async def dashboard(state: FinAgentState) -> dict:
        try:
            await push_update(state, ws_manager)
            return {"completed_agents": ["dashboard"]}
        except Exception as exc:
            logger.error("[Dashboard] failed: %s", exc)
            return {}

    return dashboard


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph(db_session_factory, ws_manager):
    graph = StateGraph(FinAgentState)

    graph.add_node("data_ingestion", make_ingestion_node(db_session_factory, run_id_getter=None))
    graph.add_node("analysis_agent", make_analysis_node(db_session_factory))
    graph.add_node("report_generator", make_report_node(db_session_factory))
    graph.add_node("notification", make_notification_node())
    graph.add_node("audit", make_audit_node(db_session_factory))
    graph.add_node("dashboard", make_dashboard_node(ws_manager))

    graph.set_entry_point("data_ingestion")
    
    def route_after_ingestion(state: FinAgentState) -> str:
        if state.get("status") == "failed":
            return "audit"
        return "analysis_agent"
        
    graph.add_conditional_edges("data_ingestion", route_after_ingestion)

    graph.add_edge("analysis_agent", "report_generator")
    graph.add_edge("report_generator", "notification")
    graph.add_edge("notification", "audit")
    graph.add_edge("audit", "dashboard")
    graph.add_edge("dashboard", END)

    return graph.compile()
