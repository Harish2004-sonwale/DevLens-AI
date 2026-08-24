"""
DevLens AI — /api/analyze, /api/analyze/improve, and /api/detect-language routes.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.models.database import ConversionHistory, get_db
from backend.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DetectLanguageRequest,
    DetectLanguageResponse,
    ImproveCodeRequest,
    ImproveCodeResponse,
    QualityDimension,
)
from backend.services.analyzer import run_analysis, run_code_improvement
from backend.services.detector import run_detection
from backend.services.validator import (
    validate_analysis,
    validate_detection,
    validate_improve_code,
)
from backend.utils.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/detect-language",
    response_model=DetectLanguageResponse,
    summary="Auto-detect programming language",
)
@limiter.limit("60/minute")
async def detect_language(
    request: Request,
    payload: DetectLanguageRequest = Body(...),
) -> DetectLanguageResponse:
    """Detect the programming language of the provided source code in <0.02s."""
    try:
        result = run_detection(payload.source_code)
        validate_detection(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return DetectLanguageResponse(**result)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze code quality",
)
@limiter.limit("20/minute")
async def analyze_code(
    request: Request,
    payload: AnalyzeRequest = Body(...),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    """Analyze code quality across 5 dimensions with deterministic weighted scoring."""
    try:
        result = run_analysis(payload.source_code, payload.language)
        validate_analysis(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    overall_score = result.get("overall_score", 0.0)

    entry = ConversionHistory(
        source_language=payload.language,
        target_language=None,
        source_code=payload.source_code,
        converted_code=f"Quality score: {overall_score:.1f}/100",
        operation="analyze",
        status="success",
        quality_score=overall_score,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    dimensions = [
        QualityDimension(**d) for d in result.get("dimensions", [])
    ]
    result["history_id"] = entry.id
    result["dimensions"] = dimensions

    return AnalyzeResponse(**result)


@router.post(
    "/analyze/improve",
    response_model=ImproveCodeResponse,
    summary="Improve code based on quality analysis",
)
@limiter.limit("15/minute")
async def improve_code(
    request: Request,
    payload: ImproveCodeRequest = Body(...),
    db: Session = Depends(get_db),
) -> ImproveCodeResponse:
    """Refactor code to address quality recommendations."""
    try:
        result = run_code_improvement(
            source_code=payload.source_code,
            language=payload.language,
            recommendations=payload.recommendations,
        )
        validate_improve_code(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    entry = ConversionHistory(
        source_language=payload.language,
        target_language=payload.language,
        source_code=payload.source_code,
        converted_code=result.get("improved_code", payload.source_code),
        operation="analyze_improve",
        status="success",
        explanation=result.get("improvement_summary", ""),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    result["history_id"] = entry.id
    return ImproveCodeResponse(**result)
