"""
Analysis Agent — Phase 5
=========================
A ReAct-style agent that dynamically analyzes a business's financial data
using available tools. Unlike the old fixed DAG, this agent decides what to
investigate based on what it finds.

Workflow:
1. Run compute_pnl to get the big picture.
2. If anomalies exist, find them.
3. If margin is dropping, compare periods.
4. If burn rate is high, compute runway.
5. Get category trends for big expenses.
6. Call generate_analysis_report tool to output structured findings.
"""

import json
import logging
import operator
from typing import Annotated, Any

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from typing_extensions import TypedDict

logger = logging.getLogger("agents.analysis_agent")

ANALYSIS_SYSTEM_PROMPT = """You are CashPilot's expert financial analysis agent.
Analyze this business's financial data.

Your goal: Find the 3-5 most important financial insights.
Strategy:
1. Start with `compute_pnl` to get the big picture (use period='last_30d' or similar).
2. Run `find_anomalies` to check for outliers or unusual spending.
3. If margin is declining or expenses are up, dig deeper with `compare_periods`.
4. If burn rate is high, or they are spending a lot, `compute_runway`.
5. Check `get_category_trends` for the largest expense categories.

Stop when you have 3-5 clear, data-backed insights.
When you are done, you MUST call the `submit_findings` tool with your findings.
Each finding should be a clear, actionable sentence with specific numbers.
"""

MAX_ITERATIONS = 10


# ── Internal State ────────────────────────────────────────────────────────────

class AnalysisState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    findings: list[str]


# ── Agent builder ─────────────────────────────────────────────────────────────

def build_analysis_graph(db, business_id: str) -> Any:
    from agents.chat_tools_lc import build_chat_tools
    from tools.llm_with_tools import get_llm_with_tools

    # Get the same financial tools used by the chat agent
    base_tools = build_chat_tools(db, business_id)

    @tool
    def submit_findings(insights: list[str]) -> str:
        """Submit the final analysis findings. Call this when you have 3-5 clear insights."""
        # This tool doesn't do much on its own, its arguments are extracted later
        return json.dumps({"status": "success", "insights_submitted": len(insights)})

    tools = base_tools + [submit_findings]
    llm_with_tools = get_llm_with_tools(tools)
    tool_node = ToolNode(tools)

    async def call_model(state: AnalysisState) -> dict:
        messages = state["messages"]
        if not messages:
            messages = [SystemMessage(content=ANALYSIS_SYSTEM_PROMPT), HumanMessage(content="Begin analysis.")]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def should_continue(state: AnalysisState) -> str:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            # Check if they called submit_findings
            for tc in last.tool_calls:
                if tc["name"] == "submit_findings":
                    return END  # End early if findings are submitted
            return "tools"
        return END

    graph = StateGraph(AnalysisState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


async def run_analysis(db, business_id: str) -> list[str]:
    """
    Run the ReAct analysis agent to explore the data and produce findings.
    Returns a list of string insights.
    """
    graph = build_analysis_graph(db, business_id)
    initial_state = {
        "messages": [
            SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content="Please analyze the recent financial data and submit findings.")
        ],
        "findings": []
    }

    try:
        result = await graph.ainvoke(initial_state, config={"recursion_limit": MAX_ITERATIONS * 2 + 2})
    except Exception as exc:
        logger.error("[AnalysisAgent] Graph execution failed: %s", exc)
        return ["Analysis failed due to an internal error."]

    # Extract the findings from the tool call to 'submit_findings'
    findings = []
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc["name"] == "submit_findings":
                    args = tc.get("args", {})
                    findings = args.get("insights", [])
                    break
        if findings:
            break

    if not findings:
        # Fallback if the agent didn't use the tool properly
        findings = ["The agent completed analysis but did not output structured findings."]

    logger.info("[AnalysisAgent] Finished with %d findings.", len(findings))
    return findings
