"""
DevLens AI — High-Speed Gemini API service.

All interactions with the Google Gemini API happen here.
Uses ultra-low latency model (gemini-3.5-flash-lite) and prompt caching for sub-2s responses.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any, List, Optional

import google.genai as genai
from dotenv import load_dotenv

from backend.models.schemas import DEFAULT_FRAMEWORKS
from backend.utils.prompts import (
    ANALYZE_PROMPT,
    DEBUG_FIX_PROMPT,
    DEBUG_PROMPT,
    DETECT_LANGUAGE_PROMPT,
    EXPLAIN_PROMPT,
    GENERATE_TESTS_PROMPT,
    IMPROVE_CODE_PROMPT,
    OPTIMIZE_PROMPT,
    SYSTEM_PERSONA,
    TRANSLATE_PROMPT,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini client initialization
# ---------------------------------------------------------------------------

_API_KEY = os.getenv("GEMINI_API_KEY")
if not _API_KEY:
    logger.warning("GEMINI_API_KEY not set. AI features will be unavailable.")

_CLIENT: genai.Client | None = None


def _get_client() -> genai.Client:
    """Return a cached Gemini client, initializing if necessary."""
    global _CLIENT
    if _CLIENT is None:
        if not _API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Set it in the .env file and restart the server."
            )
        _CLIENT = genai.Client(api_key=_API_KEY)
    return _CLIENT


# Ultra-low latency model default
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash-lite")
TIMEOUT_SECONDS = 30

# In-memory response cache
_PROMPT_CACHE: dict[str, dict[str, Any]] = {}
_MAX_CACHE_SIZE = 256


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> str:
    """
    Extract a JSON object from text that may contain Markdown fences
    or surrounding prose.
    """
    # Try to find JSON inside code fences first
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    # Otherwise look for the outermost { ... }
    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        return brace_match.group(1)

    return text


def _call_gemini(prompt: str) -> dict[str, Any]:
    """
    Make a call to the Gemini API with caching and low-latency parameters.
    Raises RuntimeError on API failure or invalid JSON response.
    """
    cache_key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if cache_key in _PROMPT_CACHE:
        logger.info("Serving response from in-memory cache (0ms)")
        return _PROMPT_CACHE[cache_key].copy()

    client = _get_client()
    model = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash-lite")
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PERSONA,
                temperature=0.1,
                max_output_tokens=8192,
                http_options={"timeout": TIMEOUT_SECONDS * 1000},
            ),
        )
    except Exception as exc:
        logger.error("Gemini API call failed: %s", type(exc).__name__)
        raise RuntimeError(
            "Gemini API is currently unavailable. Please try again shortly."
        ) from exc

    raw_text = response.text or ""
    cleaned = _extract_json(raw_text)

    try:
        parsed = json.loads(cleaned)
        # Store in cache
        if len(_PROMPT_CACHE) >= _MAX_CACHE_SIZE:
            _PROMPT_CACHE.pop(next(iter(_PROMPT_CACHE)))
        _PROMPT_CACHE[cache_key] = parsed
        return parsed
    except json.JSONDecodeError as exc:
        logger.error(
            "Gemini returned non-JSON response. Raw: %s",
            raw_text[:500],
        )
        raise RuntimeError(
            "The AI returned an unexpected response. Please try again."
        ) from exc


# ---------------------------------------------------------------------------
# Public service methods
# ---------------------------------------------------------------------------


def translate_code(
    source_code: str,
    source_language: str,
    target_language: str,
    preserve_comments: bool = True,
) -> dict[str, Any]:
    """Translate source code from one language to another."""
    preserve_instruction = (
        "9. Preserve and adapt all comments from the original code."
        if preserve_comments
        else "9. Comments from the original code can be omitted."
    )
    prompt = TRANSLATE_PROMPT.format(
        source_language=source_language,
        target_language=target_language,
        source_code=source_code,
        preserve_instruction=preserve_instruction,
    )
    return _call_gemini(prompt)


def detect_language(source_code: str) -> dict[str, Any]:
    """Detect the programming language of the given source code."""
    prompt = DETECT_LANGUAGE_PROMPT.format(source_code=source_code)
    return _call_gemini(prompt)


def explain_code(source_code: str, language: str) -> dict[str, Any]:
    """Generate a detailed explanation of source code with walkthrough and edge cases."""
    prompt = EXPLAIN_PROMPT.format(source_code=source_code, language=language)
    return _call_gemini(prompt)


def debug_code(source_code: str, language: str) -> dict[str, Any]:
    """Detect bugs, vulnerabilities, and issues in source code."""
    prompt = DEBUG_PROMPT.format(source_code=source_code, language=language)
    return _call_gemini(prompt)


def fix_bugs(
    source_code: str, language: str, issues_summary: Optional[str] = None
) -> dict[str, Any]:
    """Generate clean corrected code repairing all identified bugs."""
    issues_text = issues_summary or "Fix all syntax errors, logic bugs, unhandled edge cases, and vulnerabilities."
    prompt = DEBUG_FIX_PROMPT.format(
        language=language,
        source_code=source_code,
        issues_text=issues_text,
    )
    return _call_gemini(prompt)


def optimize_code(
    source_code: str, language: str, focus: str = "balanced"
) -> dict[str, Any]:
    """Optimize source code while preserving behavior and tracking complexity."""
    prompt = OPTIMIZE_PROMPT.format(
        source_code=source_code, language=language, focus=focus
    )
    return _call_gemini(prompt)


def improve_code(
    source_code: str, language: str, recommendations: List[str]
) -> dict[str, Any]:
    """Refactor code to improve readability, maintainability, performance, security, and complexity."""
    recs_text = "\n".join(f"- {r}" for r in recommendations) if recommendations else "Apply general code quality best practices."
    prompt = IMPROVE_CODE_PROMPT.format(
        language=language,
        source_code=source_code,
        recommendations_text=recs_text,
    )
    return _call_gemini(prompt)


def generate_tests(
    source_code: str, language: str, framework: Optional[str] = None
) -> dict[str, Any]:
    """Generate comprehensive, runnable test cases with framework conventions."""
    target_framework = framework or DEFAULT_FRAMEWORKS.get(language, "standard test framework")
    prompt = GENERATE_TESTS_PROMPT.format(
        source_code=source_code,
        language=language,
        framework=target_framework,
    )
    return _call_gemini(prompt)


def analyze_code(source_code: str, language: str) -> dict[str, Any]:
    """Perform a 5-dimension code quality analysis."""
    prompt = ANALYZE_PROMPT.format(source_code=source_code, language=language)
    return _call_gemini(prompt)


def is_configured() -> bool:
    """Return True if the Gemini API key is configured."""
    return bool(_API_KEY)
