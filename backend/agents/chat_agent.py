"""
Chat Agent — Phase 4
======================
ReAct chat agent using LangGraph + LangChain tool-calling.

Architecture:
    User message
        ↓
    [agent] — LLM decides which tool(s) to call
        ↓
    [tools] — execute tool, return result
        ↓
    [agent] — LLM synthesizes final answer
        ↓
    Response (with tools_used metadata)

The graph loops agent→tools→agent until the LLM produces a final
text response (no tool_calls in the last message).

State includes:
    messages  — conversation history (LangChain BaseMessage list)
    business_id — UUID of the business profile
    session_id  — UUID string for conversation continuity

Memory:
    - Redis: last 20 messages (context window), 24hr TTL
    - PostgreSQL: full history in chat_messages table (permanent)
"""

import json
import logging
import operator
import uuid as uuid_mod
from typing import Annotated, Any

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from typing_extensions import TypedDict

logger = logging.getLogger("agents.chat_agent")

SYSTEM_PROMPT = """You are CashPilot, a financial co-pilot for small businesses.
You have access to tools that query the user's REAL financial data.

Rules:
1. ALWAYS use at least one tool before answering financial questions. Never guess numbers.
2. Be specific — use actual dollar amounts and percentages from the tool results.
3. Keep answers concise (2-4 sentences) unless they ask for detail or a full breakdown.
4. If a question is ambiguous, pick the most useful interpretation and answer it.
5. If data is insufficient, say so honestly and suggest what data would help.
6. Format numbers with $ and commas (e.g. $12,450). Use % for percentages.
7. When you find anomalies or risks, be direct and actionable.
"""

MAX_TOOL_ITERATIONS = 8  # safety cap to prevent infinite loops


# ── State ─────────────────────────────────────────────────────────────────────

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    business_id: str
    session_id: str


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_chat_graph(tools: list) -> Any:
    """
    Build and compile the ReAct chat LangGraph.
    `tools` must be a list of LangChain @tool-decorated callables.
    """
    from tools.llm_with_tools import get_llm_with_tools

    llm_with_tools = get_llm_with_tools(tools)
    tool_node = ToolNode(tools)

    async def call_model(state: ChatState) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def should_continue(state: ChatState) -> str:
        """Route: if the LLM wants to call tools → 'tools', else → END."""
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(ChatState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END},
    )
    graph.add_edge("tools", "agent")
    return graph.compile()


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_chat(
    message: str,
    session_id: str,
    db,
    business_id,
) -> dict:
    """
    Process one user message through the ReAct chat agent.

    Returns:
        {
            "response": str,          # final assistant text
            "tools_used": list[str],  # names of tools invoked
            "session_id": str,        # echoed back for client
            "message_count": int,     # total messages in this turn
        }
    """
    from db.redis_client import load_chat_history, save_chat_history
    from agents.chat_tools_lc import build_chat_tools
    from db.models import ChatMessage, AsyncSessionLocal

    # Build tools bound to this session's db + business_id
    tools = build_chat_tools(db, business_id)

    # Load conversation history from Redis
    history: list[BaseMessage] = await load_chat_history(session_id)
    history.append(HumanMessage(content=message))

    initial_state: ChatState = {
        "messages": history,
        "business_id": str(business_id) if business_id else "",
        "session_id": session_id,
    }

    # Run the ReAct graph (bounded by MAX_TOOL_ITERATIONS)
    graph = build_chat_graph(tools)
    try:
        result = await graph.ainvoke(
            initial_state,
            config={"recursion_limit": MAX_TOOL_ITERATIONS * 2 + 2},
        )
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        logger.error("[ChatAgent] Graph execution failed: %s\n%s", exc, tb)
        return {
            "response": f"I encountered an error while processing your request: {str(exc)}",
            "tools_used": [],
            "session_id": session_id,
            "message_count": 1,
            "error": str(exc),
            "traceback": tb,
            "is_error": True,
        }

    all_messages: list[BaseMessage] = result["messages"]

    # Extract final assistant response
    final_msg = all_messages[-1]
    response_text = (
        final_msg.content
        if hasattr(final_msg, "content") and isinstance(final_msg.content, str)
        else str(final_msg.content)
    )

    # Collect tool names used in this turn
    tools_used = [
        tc["name"]
        for msg in all_messages
        if isinstance(msg, AIMessage) and msg.tool_calls
        for tc in msg.tool_calls
    ]

    # Persist updated history to Redis (last 20 messages, 24hr TTL)
    await save_chat_history(session_id, all_messages)

    # Persist to PostgreSQL (permanent record)
    if business_id is not None:
        try:
            async with AsyncSessionLocal() as persist_db:
                persist_db.add(ChatMessage(
                    id=uuid_mod.uuid4(),
                    business_id=business_id,
                    session_id=session_id,
                    role="user",
                    content=message,
                    tool_calls_json=None,
                ))
                persist_db.add(ChatMessage(
                    id=uuid_mod.uuid4(),
                    business_id=business_id,
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    tool_calls_json=tools_used if tools_used else None,
                ))
                await persist_db.commit()
        except Exception as db_exc:
            logger.warning("[ChatAgent] Failed to persist chat to DB (non-fatal): %s", db_exc)

    logger.info(
        "[ChatAgent] session=%s  tools=%s  response_len=%d",
        session_id, tools_used, len(response_text),
    )

    return {
        "response": response_text,
        "tools_used": tools_used,
        "session_id": session_id,
        "message_count": len(all_messages),
    }
