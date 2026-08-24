"""
DevLens AI — /api/convert route.
Handles code translation between supported languages.
"""

import json
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.models.database import ConversionHistory, get_db
from backend.models.schemas import ErrorResponse, TranslateRequest, TranslateResponse
from backend.services import gemini_service
from backend.services.translator import run_translation
from backend.utils.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/convert",
    response_model=TranslateResponse,
    summary="Translate code between languages",
)
@limiter.limit("20/minute")
async def convert_code(
    request: Request,
    payload: TranslateRequest = Body(...),
    db: Session = Depends(get_db),
) -> TranslateResponse:
    """
    Translate source code from one programming language to another.
    Results are saved to the conversion history.
    """
    if payload.source_language == payload.target_language:
        raise HTTPException(
            status_code=400,
            detail="Source and target languages must be different.",
        )

    try:
        result = run_translation(payload)
    except RuntimeError as exc:
        _save_history(
            db,
            source_language=payload.source_language,
            target_language=payload.target_language,
            source_code=payload.source_code,
            converted_code=None,
            operation="translate",
            status="error",
        )
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    history_entry = _save_history(
        db,
        source_language=result["source_language"],
        target_language=result["target_language"],
        source_code=payload.source_code,
        converted_code=result["converted_code"],
        operation="translate",
        status="success",
        quality_score=result.get("quality_score"),
        warnings=result.get("warnings", []),
        explanation=result.get("explanation", ""),
    )

    result["history_id"] = history_entry.id
    return TranslateResponse(**result)


def _save_history(
    db: Session,
    source_language: str,
    target_language: str | None,
    source_code: str,
    converted_code: str | None,
    operation: str,
    status: str,
    quality_score: float | None = None,
    explanation: str | None = None,
    warnings: list | None = None,
) -> ConversionHistory:
    entry = ConversionHistory(
        source_language=source_language,
        target_language=target_language,
        source_code=source_code,
        converted_code=converted_code,
        operation=operation,
        status=status,
        quality_score=quality_score,
        explanation=explanation,
        warnings=json.dumps(warnings) if warnings else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
