"""
DevLens AI — /api/debug and /api/debug/fix routes.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.models.database import ConversionHistory, get_db
from backend.models.schemas import (
    BugItem,
    DebugRequest,
    DebugResponse,
    FixBugsRequest,
    FixBugsResponse,
)
from backend.services import gemini_service
from backend.services.validator import validate_debug, validate_fix_bugs
from backend.utils.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/debug", response_model=DebugResponse, summary="Find bugs in source code")
@limiter.limit("20/minute")
async def debug_code(
    request: Request,
    payload: DebugRequest = Body(...),
    db: Session = Depends(get_db),
) -> DebugResponse:
    """Detect bugs, vulnerabilities, and code quality issues."""
    try:
        raw = gemini_service.debug_code(payload.source_code, payload.language)
        validate_debug(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    bugs_raw = raw.get("bugs", [])
    bugs = []
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0

    for b in bugs_raw:
        if isinstance(b, dict):
            severity = b.get("severity", "medium").lower()
            if severity == "critical":
                critical_count += 1
            elif severity == "high":
                high_count += 1
            elif severity == "medium":
                medium_count += 1
            else:
                low_count += 1

            bugs.append(
                BugItem(
                    line_number=b.get("line_number"),
                    issue=b.get("issue", "Identified issue"),
                    severity=severity,
                    explanation=b.get("explanation", ""),
                    recommendation=b.get("recommendation", ""),
                    suggested_fix=b.get("suggested_fix", ""),
                )
            )

    entry = ConversionHistory(
        source_language=payload.language,
        target_language=None,
        source_code=payload.source_code,
        converted_code=f"Found {len(bugs)} issue(s) ({critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low).",
        operation="debug",
        status="success",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return DebugResponse(
        success=True,
        language=payload.language,
        bugs=bugs,
        total_issues=len(bugs),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        summary=raw.get("summary", ""),
        history_id=entry.id,
        corrected_code=None,
        fixed_code=None,
    )


@router.post("/debug/fix", response_model=FixBugsResponse, summary="Fix all identified bugs with AI")
@limiter.limit("15/minute")
async def fix_code_bugs(
    request: Request,
    payload: FixBugsRequest = Body(...),
    db: Session = Depends(get_db),
) -> FixBugsResponse:
    """Repair all identified bugs and generate clean, corrected code."""
    try:
        raw = gemini_service.fix_bugs(
            source_code=payload.source_code,
            language=payload.language,
            issues_summary=payload.issues_summary,
        )
        validate_fix_bugs(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    fixed_code = raw.get("fixed_code", payload.source_code)

    entry = ConversionHistory(
        source_language=payload.language,
        target_language=payload.language,
        source_code=payload.source_code,
        converted_code=fixed_code,
        operation="debug_fix",
        status="success",
        explanation=raw.get("fix_summary", ""),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return FixBugsResponse(
        success=True,
        language=payload.language,
        original_code=payload.source_code,
        fixed_code=fixed_code,
        fix_summary=raw.get("fix_summary", "Bugs repaired successfully."),
        fixed_issues_count=int(raw.get("fixed_issues_count", 1)),
        history_id=entry.id,
    )
