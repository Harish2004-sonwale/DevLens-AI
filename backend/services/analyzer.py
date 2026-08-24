"""
DevLens AI — Code Quality Analysis and Automated Improvement service.
Implements deterministic weighted quality scoring:
Overall = 25% Security + 20% Performance + 20% Readability + 20% Maintainability + 15% Complexity
"""

import logging
from typing import Any, List, Optional

from backend.models.schemas import DIMENSION_WEIGHTS
from backend.services import gemini_service

logger = logging.getLogger(__name__)


def calculate_weighted_score(dimensions: list[dict[str, Any]]) -> float:
    """
    Deterministically calculate the overall quality score using weighted dimensions:
    Security: 25%, Performance: 20%, Readability: 20%, Maintainability: 20%, Complexity: 15%.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    score_map = {d.get("name", "").strip().capitalize(): float(d.get("score", 0.0)) for d in dimensions}

    for dim_name, weight in DIMENSION_WEIGHTS.items():
        if dim_name in score_map:
            score = max(0.0, min(100.0, score_map[dim_name]))
            weighted_sum += score * weight
            total_weight += weight

    if total_weight > 0:
        return round(weighted_sum / total_weight, 1)

    # Fallback to simple average if dimensions are unmapped
    if dimensions:
        raw_scores = [float(d.get("score", 0.0)) for d in dimensions]
        return round(sum(raw_scores) / len(raw_scores), 1)

    return 0.0


def run_analysis(source_code: str, language: str) -> dict[str, Any]:
    """Run code quality analysis with deterministic weighted scoring."""
    raw = gemini_service.analyze_code(source_code, language)

    dimensions = []
    for dim in raw.get("dimensions", []):
        if isinstance(dim, dict):
            name = dim.get("name", "Unknown").strip().capitalize()
            weight = DIMENSION_WEIGHTS.get(name, 0.20)
            score = float(dim.get("score", 0.0))
            dimensions.append(
                {
                    "name": name,
                    "score": max(0.0, min(100.0, score)),
                    "weight": weight,
                    "description": dim.get("description", ""),
                }
            )

    # Compute deterministic weighted score
    overall_score = calculate_weighted_score(dimensions)

    return {
        "success": True,
        "language": language,
        "overall_score": overall_score,
        "scoring_model": "Deterministic Weighted Model (Security 25%, Performance 20%, Readability 20%, Maintainability 20%, Complexity 15%)",
        "dimensions": dimensions,
        "recommendations": raw.get("recommendations", []),
        "summary": raw.get("summary", ""),
    }


def run_code_improvement(
    source_code: str, language: str, recommendations: Optional[List[str]] = None
) -> dict[str, Any]:
    """Run AI code refactoring based on quality recommendations."""
    raw = gemini_service.improve_code(source_code, language, recommendations or [])

    return {
        "success": True,
        "language": language,
        "original_code": source_code,
        "improved_code": raw.get("improved_code", source_code),
        "improvements_applied": raw.get("improvements_applied", []),
        "improvement_summary": raw.get("improvement_summary", ""),
    }
