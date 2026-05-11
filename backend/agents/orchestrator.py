"""
Agent 1 — Orchestrator
Initialises pipeline state. Pure Python — no LLM call.
Routing is handled by LangGraph conditional edges, not an LLM.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("agent.orchestrator")


async def initialize(state: dict) -> dict:
    """
    Sets up initial pipeline state fields.
    Called as the first LangGraph node before any agent runs.
    """
    logger.info(
        "[Orchestrator] Pipeline started — run_id=%s  triggered_by=%s",
        state.get("run_id"),
        state.get("triggered_by", "unknown"),
    )
    state.setdefault("errors", [])
    state.setdefault("completed_agents", [])
    state["status"] = "running"
    state["started_at"] = datetime.now(timezone.utc).isoformat()
    return state
