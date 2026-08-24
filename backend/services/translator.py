"""
DevLens AI — Translation service orchestration layer.
Coordinates between the API layer and Gemini service for code translation.
"""

import logging
import time
from typing import Any

from backend.models.schemas import TranslateRequest
from backend.services import gemini_service

logger = logging.getLogger(__name__)


def run_translation(request: TranslateRequest) -> dict[str, Any]:
    """
    Orchestrate a translation request:
    1. Call Gemini service
    2. Validate the response structure
    3. Return a normalized dict matching TranslateResponse
    """
    start = time.monotonic()

    raw = gemini_service.translate_code(
        source_code=request.source_code,
        source_language=request.source_language,
        target_language=request.target_language,
        preserve_comments=request.preserve_comments,
    )

    elapsed_ms = (time.monotonic() - start) * 1000

    if not raw.get("converted_code"):
        raise ValueError("Gemini returned an empty translation.")

    return {
        "success": raw.get("success", True),
        "source_language": request.source_language,
        "target_language": request.target_language,
        "converted_code": raw.get("converted_code", ""),
        "explanation": raw.get("explanation", ""),
        "warnings": raw.get("warnings", []),
        "quality_score": raw.get("quality_score"),
        "execution_time_ms": round(elapsed_ms, 2),
    }
