"""
F4 — Unit tests for the LLM Router.
Mocks all provider clients — no real API calls made.

Run:
    cd backend && python -m pytest tests/test_llm_router.py -v
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestBuildProviderChain:

    def test_groq_first_when_key_set(self):
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "gsk_test",
            "GEMINI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "OLLAMA_BASE_URL": "",
        }):
            from tools.llm_router import _build_provider_chain
            chain = _build_provider_chain()
            assert chain[0].name == "groq"

    def test_prefer_provider_moves_to_front(self):
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "gsk_test",
            "GEMINI_API_KEY": "AIza_test",
            "ANTHROPIC_API_KEY": "",
            "OLLAMA_BASE_URL": "",
        }):
            from tools.llm_router import _build_provider_chain
            chain = _build_provider_chain(prefer_provider="gemini")
            assert chain[0].name == "gemini"
            assert chain[1].name == "groq"

    def test_no_providers_raises_runtime_error(self):
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "",
            "GEMINI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "OLLAMA_BASE_URL": "",
        }):
            from tools.llm_router import _build_provider_chain
            with pytest.raises(RuntimeError, match="No LLM provider configured"):
                _build_provider_chain()

    def test_all_three_in_priority_order(self):
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "gsk_test",
            "GEMINI_API_KEY": "AIza_test",
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "OLLAMA_BASE_URL": "",
        }):
            from tools.llm_router import _build_provider_chain
            names = [p.name for p in _build_provider_chain()]
            assert names[0] == "groq"
            assert names[1] == "gemini"
            assert names[2] == "anthropic"


class TestRunAgent:

    def test_groq_called_first_and_returns_result(self):
        async def mock_complete(self_mock, system, user, max_tokens):
            return "LLM analysis complete.", 100

        with patch.dict(os.environ, {
            "GROQ_API_KEY": "gsk_test",
            "GEMINI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "OLLAMA_BASE_URL": "",
        }):
            with patch("tools.llm_router.cache_get", new=AsyncMock(return_value=None)):
                with patch("tools.llm_router.cache_set", new=AsyncMock()):
                    with patch("tools.llm_router.GroqProvider.complete", new=mock_complete):
                        from tools.llm_router import run_agent
                        result = run(run_agent(
                            system_prompt="You are a test.",
                            context={"test": True},
                            use_cache=False,
                        ))

        assert result["provider"] == "groq"
        assert result["tokens_used"] == 100
        assert result["cached"] is False

    def test_fallback_to_gemini_when_groq_fails(self):
        async def groq_fail(self_mock, system, user, max_tokens):
            raise ConnectionError("Rate limited")

        async def gemini_ok(self_mock, system, user, max_tokens):
            return "Gemini fallback.", 80

        with patch.dict(os.environ, {
            "GROQ_API_KEY": "gsk_test",
            "GEMINI_API_KEY": "AIza_test",
            "ANTHROPIC_API_KEY": "",
            "OLLAMA_BASE_URL": "",
        }):
            with patch("tools.llm_router.cache_get", new=AsyncMock(return_value=None)):
                with patch("tools.llm_router.cache_set", new=AsyncMock()):
                    with patch("tools.llm_router.GroqProvider.complete", new=groq_fail):
                        with patch("tools.llm_router.GeminiProvider.complete", new=gemini_ok):
                            from tools.llm_router import run_agent
                            result = run(run_agent(
                                system_prompt="Test", context={}, use_cache=False
                            ))

        assert result["provider"] == "gemini"

    def test_cache_hit_skips_provider(self):
        cached = {
            "text": "cached", "tokens_used": 50,
            "provider": "groq", "cached": False, "duration_ms": 100,
        }
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}):
            with patch("tools.llm_router.cache_get", new=AsyncMock(return_value=cached)):
                from tools.llm_router import run_agent
                result = run(run_agent(
                    system_prompt="Test", context={}, use_cache=True
                ))
        assert result["cached"] is True

    def test_all_providers_fail_returns_fallback(self):
        async def always_fail(self_mock, system, user, max_tokens):
            raise RuntimeError("down")

        with patch.dict(os.environ, {
            "GROQ_API_KEY": "gsk_test",
            "GEMINI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "OLLAMA_BASE_URL": "",
        }):
            with patch("tools.llm_router.cache_get", new=AsyncMock(return_value=None)):
                with patch("tools.llm_router.cache_set", new=AsyncMock()):
                    with patch("tools.llm_router.GroqProvider.complete", new=always_fail):
                        from tools.llm_router import run_agent
                        result = run(run_agent(
                            system_prompt="Test", context={}, use_cache=False
                        ))
                        
        assert result["provider"] == "synthetic_fallback"
        assert "synthetic fallback" in result["text"]
