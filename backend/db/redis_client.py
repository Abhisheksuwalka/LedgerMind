"""
Redis client — shared cache layer for agent outputs.
Cache TTL: 1 hour by default (cost-controls for Claude API).
"""

import json
import os
from typing import Any, Optional

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DEFAULT_TTL = 3600  # 1 hour

_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return _pool


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    r = await get_redis()
    await r.set(key, json.dumps(value), ex=ttl)


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    raw = await r.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)


async def publish_event(channel: str, event: dict):
    """Publish real-time events to Redis pub/sub (picked up by Dashboard Agent)."""
    r = await get_redis()
    await r.publish(channel, json.dumps(event))


# ── Chat history (Phase 4) ────────────────────────────────────────────────────

CHAT_TTL = 86400  # 24 hours


def _serialize_message(msg) -> str:
    """Serialize a LangChain BaseMessage to a JSON string for Redis storage."""
    return json.dumps({
        "type": msg.__class__.__name__,   # HumanMessage | AIMessage | ToolMessage | SystemMessage
        "content": msg.content,
        "tool_calls": getattr(msg, "tool_calls", None),
        "tool_call_id": getattr(msg, "tool_call_id", None),
        "name": getattr(msg, "name", None),
    })


def _deserialize_message(raw: str):
    """Deserialize a JSON string back to the appropriate LangChain message type."""
    from langchain_core.messages import (
        AIMessage, HumanMessage, SystemMessage, ToolMessage
    )
    data = json.loads(raw)
    msg_type = data.get("type", "HumanMessage")
    content = data.get("content", "")
    tool_calls = data.get("tool_calls") or []
    tool_call_id = data.get("tool_call_id")
    name = data.get("name")

    if msg_type == "HumanMessage":
        return HumanMessage(content=content)
    elif msg_type == "AIMessage":
        return AIMessage(content=content, tool_calls=tool_calls)
    elif msg_type == "ToolMessage":
        return ToolMessage(content=content, tool_call_id=tool_call_id or "", name=name)
    else:
        return HumanMessage(content=content)


async def load_chat_history(session_id: str, max_messages: int = 20) -> list:
    """
    Load the last `max_messages` messages from Redis for a session.
    Returns a list of LangChain BaseMessage objects.
    """
    try:
        r = await get_redis()
        raw_list = await r.lrange(f"chat:{session_id}", -max_messages, -1)
        return [_deserialize_message(m) for m in raw_list]
    except Exception as exc:
        import logging
        logging.getLogger("redis_client").warning(
            "[Redis] Failed to load chat history for session %s: %s", session_id, exc
        )
        return []


async def save_chat_history(session_id: str, messages: list) -> None:
    """
    Append new messages to the Redis list for this session and refresh TTL.
    Keeps only the last 100 messages to prevent unbounded growth.
    """
    try:
        r = await get_redis()
        key = f"chat:{session_id}"
        for msg in messages:
            await r.rpush(key, _serialize_message(msg))
        # Trim to last 100 messages
        await r.ltrim(key, -100, -1)
        # Refresh TTL
        await r.expire(key, CHAT_TTL)
    except Exception as exc:
        import logging
        logging.getLogger("redis_client").warning(
            "[Redis] Failed to save chat history for session %s: %s", session_id, exc
        )


async def clear_chat_history(session_id: str) -> None:
    """Delete the chat history for a session."""
    try:
        r = await get_redis()
        await r.delete(f"chat:{session_id}")
    except Exception:
        pass
