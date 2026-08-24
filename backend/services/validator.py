"""
DevLens AI — AI response validator.
Ensures Gemini responses are well-formed before being forwarded to clients.
"""

from typing import Any


def validate_translation(raw: dict[str, Any]) -> None:
    """Raise ValueError if a translation response is missing required fields."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if not raw.get("converted_code"):
        raise ValueError(
            "Gemini returned an empty or missing 'converted_code' field."
        )


def validate_detection(raw: dict[str, Any]) -> None:
    """Raise ValueError if a detection response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if "detected_language" not in raw:
        raise ValueError("Gemini response missing 'detected_language' field.")
    if "confidence" not in raw:
        raise ValueError("Gemini response missing 'confidence' field.")


def validate_explanation(raw: dict[str, Any]) -> None:
    """Raise ValueError if an explanation response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    for field in ("overview", "detailed_explanation"):
        if field not in raw:
            raise ValueError(f"Gemini explanation response missing '{field}' field.")


def validate_debug(raw: dict[str, Any]) -> None:
    """Raise ValueError if a debug response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if "bugs" not in raw:
        raise ValueError("Gemini debug response missing 'bugs' field.")


def validate_fix_bugs(raw: dict[str, Any]) -> None:
    """Raise ValueError if a fix bugs response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if "fixed_code" not in raw or not raw["fixed_code"]:
        raise ValueError("Gemini fix response missing 'fixed_code' field.")


def validate_optimization(raw: dict[str, Any]) -> None:
    """Raise ValueError if an optimization response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if "optimized_code" not in raw:
        raise ValueError("Gemini optimization response missing 'optimized_code' field.")


def validate_improve_code(raw: dict[str, Any]) -> None:
    """Raise ValueError if a code improvement response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if "improved_code" not in raw or not raw["improved_code"]:
        raise ValueError("Gemini improve response missing 'improved_code' field.")


def validate_tests(raw: dict[str, Any]) -> None:
    """Raise ValueError if a test generation response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if "test_code" not in raw:
        raise ValueError("Gemini test response missing 'test_code' field.")


def validate_analysis(raw: dict[str, Any]) -> None:
    """Raise ValueError if a quality analysis response is malformed."""
    if not isinstance(raw, dict):
        raise ValueError("Expected a JSON object from Gemini.")
    if "dimensions" not in raw and "overall_score" not in raw:
        raise ValueError("Gemini analysis response missing 'dimensions' field.")
