"""
Robust JSON extraction utilities for LLM responses.
Handles: raw JSON, JSON in markdown code fences, JSON embedded in prose.
"""

import json
import logging
import re
from typing import Optional

logger = logging.getLogger("json_utils")


def extract_json_object(text: str) -> Optional[dict]:
    """
    Try multiple strategies to extract a JSON object from LLM output.
    Returns None if all strategies fail.
    """
    if not text or not text.strip():
        return None

    # Strategy 1: full text is valid JSON
    try:
        result = json.loads(text.strip())
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Strategy 2: JSON inside markdown code fence ```json ... ``` or ``` ... ```
    fence_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE
    )
    if fence_match:
        try:
            result = json.loads(fence_match.group(1))
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    # Strategy 3: first { to last } (handles prose before/after JSON)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    logger.warning("[json_utils] Failed to extract JSON object from text (len=%d)", len(text))
    return None


def extract_json_array(text: str) -> Optional[list]:
    """
    Try multiple strategies to extract a JSON array from LLM output.
    Returns None if all strategies fail.
    """
    if not text or not text.strip():
        return None

    # Strategy 1: full text is valid JSON array
    try:
        result = json.loads(text.strip())
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Strategy 2: JSON array inside markdown code fence
    fence_match = re.search(
        r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE
    )
    if fence_match:
        try:
            result = json.loads(fence_match.group(1))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Strategy 3: first [ to last ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    logger.warning("[json_utils] Failed to extract JSON array from text (len=%d)", len(text))
    return None
