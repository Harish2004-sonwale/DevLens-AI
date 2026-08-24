"""
DevLens AI — /api/explain route.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.models.database import ConversionHistory, get_db
from backend.models.schemas import ExplainRequest, ExplainResponse
from backend.services import gemini_service
from backend.services.validator import validate_explanation
from backend.utils.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/explain", response_model=ExplainResponse, summary="Explain source code")
@limiter.limit("20/minute")
async def explain_code(
    request: Request,
    payload: ExplainRequest = Body(...),
    db: Session = Depends(get_db),
) -> ExplainResponse:
    """Generate a detailed explanation of code with walkthrough, concepts, and edge cases."""
    try:
        raw = gemini_service.explain_code(payload.source_code, payload.language)
        validate_explanation(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    overview = raw.get("overview", "")

    entry = ConversionHistory(
        source_language=payload.language,
        target_language=None,
        source_code=payload.source_code,
        converted_code=overview,
        operation="explain",
        status="success",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return ExplainResponse(
        success=True,
        language=payload.language,
        overview=overview,
        detailed_explanation=raw.get("detailed_explanation", ""),
        functions_and_classes=raw.get("functions_and_classes", []),
        important_variables=raw.get("important_variables", []),
        algorithm=raw.get("algorithm", ""),
        time_complexity=raw.get("time_complexity", "N/A"),
        space_complexity=raw.get("space_complexity", "N/A"),
        potential_issues=raw.get("potential_issues", []),
        example_walkthrough=raw.get("example_walkthrough", ""),
        concepts_used=raw.get("concepts_used", []),
        edge_cases=raw.get("edge_cases", []),
        history_id=entry.id,
    )
