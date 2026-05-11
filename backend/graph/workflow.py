"""
LangGraph state machine — orchestrates all 10 agents.
Each node receives and mutates the shared FinAgentState TypedDict.
"""

import logging
import operator
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

    # agent outputs
    ingestion_result: dict
    pnl_result: dict
    forecast_result: dict
    anomaly_result: dict
    reconciliation_result: dict
    report_result: dict

    # control (using Annotated to merge parallel updates)
    errors: Annotated[list[dict], operator.add]
    completed_agents: Annotated[list[str], operator.add]
    status: str  # running | completed | failed
    _ws_manager: Any


# ── Node implementations (thin wrappers — real logic lives in agents/) ────────

def make_orchestrator_node():
    from agents.orchestrator import initialize

    async def orchestrator(state: FinAgentState) -> FinAgentState:
        return await initialize(state)

    return orchestrator


def make_ingestion_node(db_session_factory, run_id_getter):
    from agents.data_ingestion import ingest
    from agents.dashboard_agent import push_agent_event

    async def ingestion(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        await push_agent_event("agent_started", "data_ingestion", {}, ws)
        try:
            async with db_session_factory() as db:
                result = await ingest(
                    content=state["file_content"],
                    file_type=state.get("file_type", "csv"),
                    run_id=state.get("run_id"),
                    db=db,
                )
            await push_agent_event("agent_done", "data_ingestion",
                                   {"total_transactions": result.get("total_transactions")}, ws)
            return {"ingestion_result": result, "completed_agents": ["data_ingestion"]}
        except Exception as exc:
            logger.error("[DataIngestion] failed: %s", exc)
            await push_agent_event("agent_error", "data_ingestion", {"error": str(exc)}, ws)
            return {"errors": [{"agent": "data_ingestion", "error": str(exc)}], "status": "failed"}

    return ingestion


def make_pnl_node():
    from agents.pnl_analyzer import analyze
    from agents.dashboard_agent import push_agent_event

    async def pnl(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        await push_agent_event("agent_started", "pnl_analyzer", {}, ws)
        try:
            result = await analyze(state["ingestion_result"], state.get("run_id"))
            await push_agent_event("agent_done", "pnl_analyzer",
                                   {"health_score": result.get("health_score"),
                                    "revenue": result.get("revenue")}, ws)
            return {"pnl_result": result, "completed_agents": ["pnl_analyzer"]}
        except Exception as exc:
            logger.error("[PnLAnalyzer] failed: %s", exc)
            await push_agent_event("agent_error", "pnl_analyzer", {"error": str(exc)}, ws)
            return {"errors": [{"agent": "pnl_analyzer", "error": str(exc)}]}

    return pnl


def make_forecasting_node():
    from agents.forecasting import forecast
    from agents.dashboard_agent import push_agent_event

    async def forecasting(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        await push_agent_event("agent_started", "forecasting", {}, ws)
        try:
            result = await forecast(state["ingestion_result"], state.get("run_id"))
            await push_agent_event("agent_done", "forecasting",
                                   {"confidence": result.get("confidence_level")}, ws)
            return {"forecast_result": result, "completed_agents": ["forecasting"]}
        except Exception as exc:
            logger.error("[Forecasting] failed: %s", exc)
            await push_agent_event("agent_error", "forecasting", {"error": str(exc)}, ws)
            return {"errors": [{"agent": "forecasting", "error": str(exc)}]}

    return forecasting


def make_anomaly_node():
    from agents.anomaly_detection import detect
    from agents.dashboard_agent import push_agent_event

    async def anomaly(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        await push_agent_event("agent_started", "anomaly_detection", {}, ws)
        try:
            result = await detect(state["ingestion_result"], state.get("run_id"))
            await push_agent_event("agent_done", "anomaly_detection",
                                   {"total_flagged": result.get("total_flagged", 0)}, ws)
            return {"anomaly_result": result, "completed_agents": ["anomaly_detection"]}
        except Exception as exc:
            logger.error("[AnomalyDetection] failed: %s", exc)
            await push_agent_event("agent_error", "anomaly_detection", {"error": str(exc)}, ws)
            return {"errors": [{"agent": "anomaly_detection", "error": str(exc)}]}

    return anomaly


def make_reconciliation_node():
    from agents.reconciliation import reconcile
    from agents.dashboard_agent import push_agent_event

    async def reconciliation(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        await push_agent_event("agent_started", "reconciliation", {}, ws)
        try:
            result = await reconcile(state["ingestion_result"], state.get("run_id"))
            await push_agent_event("agent_done", "reconciliation",
                                   {"match_rate_pct": result.get("match_rate_pct")}, ws)
            return {"reconciliation_result": result, "completed_agents": ["reconciliation"]}
        except Exception as exc:
            logger.error("[Reconciliation] failed: %s", exc)
            await push_agent_event("agent_error", "reconciliation", {"error": str(exc)}, ws)
            return {"errors": [{"agent": "reconciliation", "error": str(exc)}]}

    return reconciliation


def make_report_node():
    from agents.report_generator import generate_report
    from agents.dashboard_agent import push_agent_event

    async def report(state: FinAgentState) -> dict:
        ws = state.get("_ws_manager")
        await push_agent_event("agent_started", "report_generator", {}, ws)
        try:
            result = await generate_report(state)
            await push_agent_event("agent_done", "report_generator",
                                   {"report_id": result.get("report_id")}, ws)
            return {"report_result": result, "completed_agents": ["report_generator"], "status": "completed"}
        except Exception as exc:
            logger.error("[ReportGenerator] failed: %s", exc)
            await push_agent_event("agent_error", "report_generator", {"error": str(exc)}, ws)
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


# ── Routing helpers ───────────────────────────────────────────────────────────

def route_after_ingestion(state: FinAgentState) -> list[str]:
    if state.get("status") == "failed":
        return ["audit"]
    return ["pnl_analyzer", "forecasting", "anomaly_detection", "reconciliation"]





# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph(db_session_factory, ws_manager):
    graph = StateGraph(FinAgentState)

    graph.add_node("orchestrator", make_orchestrator_node())
    graph.add_node("data_ingestion", make_ingestion_node(db_session_factory, run_id_getter=None))
    graph.add_node("pnl_analyzer", make_pnl_node())
    graph.add_node("forecasting", make_forecasting_node())
    graph.add_node("anomaly_detection", make_anomaly_node())
    graph.add_node("reconciliation", make_reconciliation_node())
    graph.add_node("report_generator", make_report_node())
    graph.add_node("notification", make_notification_node())
    graph.add_node("audit", make_audit_node(db_session_factory))
    graph.add_node("dashboard", make_dashboard_node(ws_manager))

    # Edges
    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "data_ingestion")
    graph.add_conditional_edges("data_ingestion", route_after_ingestion)

    # Fan-in: wait for all parallel analysis agents
    graph.add_edge(
        ["pnl_analyzer", "forecasting", "anomaly_detection", "reconciliation"],
        "report_generator"
    )

    graph.add_edge("report_generator", "notification")
    graph.add_edge("notification", "audit")
    graph.add_edge("audit", "dashboard")
    graph.add_edge("dashboard", END)

    return graph.compile()
