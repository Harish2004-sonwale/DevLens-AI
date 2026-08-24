"""
DevLens AI — /api/optimize route.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.models.database import ConversionHistory, get_db
from backend.models.schemas import OptimizationChange, OptimizeRequest, OptimizeResponse
from backend.services import gemini_service
from backend.services.validator import validate_optimization
from backend.utils.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/optimize", response_model=OptimizeResponse, summary="Optimize source code"
)
@limiter.limit("20/minute")
async def optimize_code(
    request: Request,
    payload: OptimizeRequest = Body(...),
    db: Session = Depends(get_db),
) -> OptimizeResponse:
    """Optimize source code while preserving behavior and analyzing complexities."""
    try:
        raw = gemini_service.optimize_code(
            payload.source_code, payload.language, payload.focus
        )
        validate_optimization(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    changes = []
    for c in raw.get("changes", []):
        if isinstance(c, dict):
            changes.append(
                OptimizationChange(
                    description=c.get("description", ""),
                    reason=c.get("reason", ""),
                    category=c.get("category", "performance"),
                )
            )

    before_time = raw.get("before_time_complexity", "N/A")
    after_time = raw.get("after_time_complexity", "N/A")
    before_space = raw.get("before_space_complexity", "N/A")
    after_space = raw.get("after_space_complexity", "N/A")

    entry = ConversionHistory(
        source_language=payload.language,
        target_language=payload.language,
        source_code=payload.source_code,
        converted_code=raw.get("optimized_code", ""),
        operation="optimize",
        status="success",
        explanation=raw.get("complexity_summary", ""),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return OptimizeResponse(
        success=True,
        language=payload.language,
        original_code=payload.source_code,
        optimized_code=raw.get("optimized_code", ""),
        before_complexity=f"Time {before_time} / Space {before_space}",
        after_complexity=f"Time {after_time} / Space {after_space}",
        before_time_complexity=before_time,
        after_time_complexity=after_time,
        before_space_complexity=before_space,
        after_space_complexity=after_space,
        complexity_summary=raw.get("complexity_summary", ""),
        changes=changes,
        performance_notes=raw.get("performance_notes", ""),
        readability_notes=raw.get("readability_notes", ""),
        history_id=entry.id,
    )
