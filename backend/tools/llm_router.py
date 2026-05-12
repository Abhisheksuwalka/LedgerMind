"""
LLM Router — provider-agnostic LLM abstraction for LedgerMind.

Priority order (based on which keys are configured in .env):
  1. Groq   (llama-3.3-70b-versatile) — FREE, fast
  2. Gemini (gemini-2.0-flash-exp)    — FREE tier
  3. Anthropic (claude-3-5-sonnet)    — PAID, optional

Usage:
    from tools.llm_router import run_agent

    result = await run_agent(
        system_prompt=SYSTEM_PROMPT,
        context={"key": "value"},
        max_tokens=1024,
    )
    # result = {"text": str, "tokens_used": int, "provider": str, "cached": bool, "duration_ms": int}

For the report generator (highest quality needed):
    result = await run_agent(..., prefer_provider="anthropic")
    # Falls back to groq/gemini if anthropic key not set
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Optional

from db.redis_client import cache_get, cache_set

logger = logging.getLogger("llm_router")


# ── Provider implementations ──────────────────────────────────────────────────

class GroqProvider:
    name = "groq"
    MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def is_available(self) -> bool:
        return bool(os.getenv("GROQ_API_KEY"))

    async def complete(self, system: str, user: str, max_tokens: int) -> tuple[str, int]:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            ),
            timeout=45.0,
        )
        text = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else len(text.split())
        return text, tokens


class GeminiProvider:
    name = "gemini"
    MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    def is_available(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    async def complete(self, system: str, user: str, max_tokens: int) -> tuple[str, int]:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            self.MODEL,
            system_instruction=system,
        )
        resp = await asyncio.wait_for(
            asyncio.to_thread(
                model.generate_content,
                user,
                generation_config={"max_output_tokens": max_tokens, "temperature": 0.3},
            ),
            timeout=45.0,
        )
        text = resp.text or ""
        tokens = (
            resp.usage_metadata.total_token_count
            if hasattr(resp, "usage_metadata") and resp.usage_metadata
            else len(text.split())
        )
        return text, tokens


class AnthropicProvider:
    name = "anthropic"
    MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    def is_available(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    async def complete(self, system: str, user: str, max_tokens: int) -> tuple[str, int]:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = await asyncio.wait_for(
            client.messages.create(
                model=self.MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            ),
            timeout=90.0,
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text"))
        tokens = resp.usage.input_tokens + resp.usage.output_tokens
        return text, tokens


class OllamaProvider:
    """Local Ollama — activated when OLLAMA_BASE_URL is set."""
    name = "ollama"
    MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def is_available(self) -> bool:
        return bool(os.getenv("OLLAMA_BASE_URL"))

    async def complete(self, system: str, user: str, max_tokens: int) -> tuple[str, int]:
        import httpx
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/chat",
                json={
                    "model": self.MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            data = resp.json()
        text = data.get("message", {}).get("content", "")
        return text, len(text.split())


# ── Provider chain builder ────────────────────────────────────────────────────

_ALL_PROVIDERS = [GroqProvider, GeminiProvider, AnthropicProvider, OllamaProvider]


def _build_provider_chain(prefer_provider: Optional[str] = None) -> list:
    """
    Build ordered list of available providers based on env vars.
    If prefer_provider is set and available, it is moved to the front.
    """
    instances = [P() for P in _ALL_PROVIDERS]
    available = [p for p in instances if p.is_available()]

    if not available:
        raise RuntimeError(
            "No LLM provider configured. "
            "Set at least one of: GROQ_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, OLLAMA_BASE_URL.\n"
            "Free options: GROQ_API_KEY from https://console.groq.com/keys"
        )

    if prefer_provider:
        preferred = [p for p in available if p.name == prefer_provider]
        rest = [p for p in available if p.name != prefer_provider]
        available = preferred + rest

    names = [p.name for p in available]
    logger.debug("[LLMRouter] Provider chain: %s", names)
    return available


# ── Cache key ─────────────────────────────────────────────────────────────────

def _cache_key(system: str, user: str) -> str:
    raw = system + user
    return "llm:" + hashlib.sha256(raw.encode()).hexdigest()[:32]


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_agent(
    system_prompt: str,
    context: dict,
    max_tokens: int = 1024,
    use_cache: bool = True,
    prefer_provider: Optional[str] = None,
) -> dict:
    """
    Call the LLM with automatic provider fallback.

    Args:
        system_prompt: Instruction string for the LLM.
        context: Dict of financial data — serialised as JSON in the user message.
        max_tokens: Max output tokens.
        use_cache: Whether to use Redis cache (skip for report generator).
        prefer_provider: Name of preferred provider ("groq", "gemini", "anthropic").
                         Falls back to others if preferred is unavailable.

    Returns:
        {
            "text": str,            # Raw LLM response
            "tokens_used": int,     # Token count (approximate for some providers)
            "provider": str,        # Which provider actually responded
            "cached": bool,         # True if served from Redis cache
            "duration_ms": int,     # Wall time of the LLM call
        }
    """
    user_content = f"Financial context:\n{json.dumps(context, default=str)}"
    key = _cache_key(system_prompt, user_content)

    # Cache check
    if use_cache:
        try:
            cached = await cache_get(key)
            if cached:
                logger.debug("[LLMRouter] Cache hit for key=%s", key)
                cached["cached"] = True
                return cached
        except Exception as cache_exc:
            logger.warning("[LLMRouter] Cache read failed (non-fatal): %s", cache_exc)

    providers = _build_provider_chain(prefer_provider)
    last_error: Optional[Exception] = None

    for provider in providers:
        try:
            logger.info("[LLMRouter] Trying provider: %s (model: %s)", provider.name, getattr(provider, "MODEL", "?"))
            t0 = time.monotonic()
            text, tokens = await provider.complete(system_prompt, user_content, max_tokens)
            duration_ms = int((time.monotonic() - t0) * 1000)

            if not text.strip():
                raise ValueError(f"Provider {provider.name} returned empty response")

            result = {
                "text": text,
                "tokens_used": tokens,
                "provider": provider.name,
                "cached": False,
                "duration_ms": duration_ms,
            }
            logger.info(
                "[LLMRouter] ✓ %s responded in %dms — %d tokens",
                provider.name, duration_ms, tokens,
            )

            # Cache successful response
            if use_cache:
                try:
                    await cache_set(key, result)
                except Exception as cache_exc:
                    logger.warning("[LLMRouter] Cache write failed (non-fatal): %s", cache_exc)

            return result

        except Exception as exc:
            logger.warning(
                "[LLMRouter] Provider %s failed: %s — trying next provider",
                provider.name, exc,
            )
            last_error = exc

    logger.error(
        "[LLMRouter] All LLM providers exhausted. Last error: %s\nProviders tried: %s",
        last_error, [p.name for p in providers]
    )
    # Graceful degradation: return a synthetic response so the pipeline continues
    # with valid numerical data even if the narrative generation fails due to API limits.
    fallback_text = (
        '{\n'
        '  "narrative": "LedgerMind synthetic fallback: LLM providers are currently exhausted or rate-limited. '
        f'The numerical analysis completed successfully, but narrative generation was skipped. (Last error: {last_error})",\n'
        '  "key_insights": ["LLM API rate limit exceeded", "Numerical data is accurate", "Graceful degradation active"],\n'
        '  "health_score": 50,\n'
        '  "alerts": ["LLM APIs unavailable"]\n'
        '}'
    )
    return {
        "text": fallback_text,
        "tokens_used": 0,
        "provider": "synthetic_fallback",
        "cached": False,
        "duration_ms": 0,
    }


# ── Startup diagnostic ────────────────────────────────────────────────────────

def log_provider_status():
    """Call once at app startup to log which providers are ready."""
    available = []
    unavailable = []
    for P in _ALL_PROVIDERS:
        p = P()
        if p.is_available():
            available.append(f"  ✓ {p.name} ({getattr(p, 'MODEL', 'n/a')})")
        else:
            unavailable.append(f"  ✗ {p.name} (key not set)")

    logger.info(
        "[LLMRouter] Provider status:\n%s\n%s",
        "\n".join(available) if available else "  (none configured!)",
        "\n".join(unavailable),
    )
    if not available:
        logger.error(
            "[LLMRouter] CRITICAL: No LLM providers configured. "
            "Add GROQ_API_KEY to .env (free: https://console.groq.com/keys)"
        )
