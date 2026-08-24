"""
DevLens AI — /api/generate-tests route.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.models.database import ConversionHistory, get_db
from backend.models.schemas import (
    DEFAULT_FRAMEWORKS,
    GenerateTestsRequest,
    GenerateTestsResponse,
    TestCase,
)
from backend.services import gemini_service
from backend.services.validator import validate_tests
from backend.utils.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/generate-tests",
    response_model=GenerateTestsResponse,
    summary="Generate test cases for source code",
)
@limiter.limit("15/minute")
async def generate_tests(
    request: Request,
    payload: GenerateTestsRequest = Body(...),
    db: Session = Depends(get_db),
) -> GenerateTestsResponse:
    """Generate comprehensive, runnable test cases with framework conventions and categorization."""
    framework = payload.framework or DEFAULT_FRAMEWORKS.get(payload.language, "standard test framework")
    try:
        raw = gemini_service.generate_tests(payload.source_code, payload.language, framework)
        validate_tests(raw)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    test_cases = []
    normal_count = 0
    edge_count = 0
    exception_count = 0
    security_count = 0
    regression_count = 0

    for tc in raw.get("test_cases", []):
        if isinstance(tc, dict):
            raw_type = str(tc.get("test_type", "normal")).lower()
            is_edge = bool(tc.get("is_edge_case", False)) or raw_type == "edge"

            if "exception" in raw_type or "error" in raw_type:
                test_type = "exception"
                exception_count += 1
            elif "security" in raw_type:
                test_type = "security"
                security_count += 1
            elif "regression" in raw_type:
                test_type = "regression"
                regression_count += 1
            elif is_edge:
                test_type = "edge"
                edge_count += 1
            else:
                test_type = "normal"
                normal_count += 1

            test_cases.append(
                TestCase(
                    name=tc.get("name", "test_case"),
                    description=tc.get("description", ""),
                    test_code=tc.get("test_code", ""),
                    expected_output=tc.get("expected_output", ""),
                    test_type=test_type,
                    is_edge_case=(test_type == "edge"),
                )
            )

    entry = ConversionHistory(
        source_language=payload.language,
        target_language=payload.language,
        source_code=payload.source_code,
        converted_code=raw.get("test_code", ""),
        operation="generate_tests",
        status="success",
        explanation=f"Generated {len(test_cases)} tests ({framework}): {normal_count} normal, {edge_count} edge, {exception_count} exception, {security_count} security.",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return GenerateTestsResponse(
        success=True,
        language=payload.language,
        test_framework=raw.get("test_framework", framework),
        test_code=raw.get("test_code", ""),
        test_cases=test_cases,
        total_count=len(test_cases),
        normal_count=normal_count,
        edge_count=edge_count,
        exception_count=exception_count,
        security_count=security_count,
        regression_count=regression_count,
        history_id=entry.id,
    )
