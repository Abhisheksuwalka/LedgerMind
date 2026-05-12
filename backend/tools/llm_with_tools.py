"""
LLM with Tool-Calling Support — Phase 4
=========================================
Returns a LangChain chat model bound to the given tools.

Priority: Groq (llama-3.3-70b-versatile) → Gemini (gemini-2.0-flash)
Both support function/tool-calling on their free tiers.

Usage:
    from tools.llm_with_tools import get_llm_with_tools
    llm = get_llm_with_tools(tools)
    response = await llm.ainvoke(messages)
"""

import logging
import os
from typing import Any

logger = logging.getLogger("tools.llm_with_tools")


def get_llm_with_tools(tools: list[Any], prefer_provider: str = "groq"):
    """
    Return a LangChain chat model with tools bound (tool_choice="auto").

    Falls back automatically: groq → gemini.
    Raises RuntimeError if no provider is configured.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if groq_key and prefer_provider == "groq":
        try:
            from langchain_groq import ChatGroq
            model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            llm = ChatGroq(
                api_key=groq_key,
                model=model_name,
                temperature=0.2,
                max_retries=2,
            )
            bound = llm.bind_tools(tools)
            logger.info("[LLMWithTools] Using Groq (%s) with %d tools", model_name, len(tools))
            return bound
        except Exception as exc:
            logger.warning("[LLMWithTools] Groq bind failed: %s — trying Gemini", exc)

    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            llm = ChatGoogleGenerativeAI(
                google_api_key=gemini_key,
                model=model_name,
                temperature=0.2,
                max_retries=2,
            )
            bound = llm.bind_tools(tools)
            logger.info("[LLMWithTools] Using Gemini (%s) with %d tools", model_name, len(tools))
            return bound
        except Exception as exc:
            logger.warning("[LLMWithTools] Gemini bind failed: %s", exc)

    raise RuntimeError(
        "No tool-calling-capable LLM configured. "
        "Set GROQ_API_KEY (free: https://console.groq.com/keys) "
        "or GEMINI_API_KEY (free: https://aistudio.google.com/apikey)."
    )
