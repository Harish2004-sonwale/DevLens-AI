import pytest
from backend.services.validator import (
    validate_translation,
    validate_detection,
    validate_explanation,
    validate_debug,
    validate_optimization,
    validate_tests,
    validate_analysis,
    validate_fix_bugs,
    validate_improve_code,
)
from backend.services.gemini_service import _extract_json
from backend.services.analyzer import calculate_weighted_score


def test_extract_json_with_code_fences():
    text = 'Here is the result:\n```json\n{"success": true, "code": "foo"}\n```\nEnjoy!'
    assert _extract_json(text) == '{"success": true, "code": "foo"}'


def test_extract_json_raw_braces():
    text = 'prefix text {"score": 90} postfix'
    assert _extract_json(text) == '{"score": 90}'


def test_validate_translation():
    validate_translation({"converted_code": "print(1)"})
    with pytest.raises(ValueError, match="empty or missing"):
        validate_translation({"converted_code": ""})
    with pytest.raises(ValueError, match="Expected a JSON object"):
        validate_translation("invalid")


def test_validate_detection():
    validate_detection({"detected_language": "python", "confidence": 0.9})
    with pytest.raises(ValueError, match="detected_language"):
        validate_detection({"confidence": 0.9})
    with pytest.raises(ValueError, match="confidence"):
        validate_detection({"detected_language": "python"})


def test_validate_explanation():
    validate_explanation({"overview": "demo", "detailed_explanation": "detail"})
    with pytest.raises(ValueError, match="overview"):
        validate_explanation({"detailed_explanation": "detail"})


def test_validate_debug():
    validate_debug({"bugs": []})
    with pytest.raises(ValueError, match="bugs"):
        validate_debug({"summary": "no bugs"})


def test_validate_optimization():
    validate_optimization({"optimized_code": "x = 1"})
    with pytest.raises(ValueError, match="optimized_code"):
        validate_optimization({})


def test_validate_tests():
    validate_tests({"test_code": "def test_foo(): pass"})
    with pytest.raises(ValueError, match="test_code"):
        validate_tests({})


def test_validate_analysis():
    validate_analysis({"overall_score": 85})
    validate_analysis({"dimensions": []})
    with pytest.raises(ValueError, match="dimensions"):
        validate_analysis({})


def test_validate_fix_and_improve():
    validate_fix_bugs({"fixed_code": "x = 1"})
    validate_improve_code({"improved_code": "x = 1"})
    with pytest.raises(ValueError, match="fixed_code"):
        validate_fix_bugs({})
    with pytest.raises(ValueError, match="improved_code"):
        validate_improve_code({})


def test_weighted_score_formula():
    dims = [
        {"name": "Readability", "score": 70},
        {"name": "Maintainability", "score": 60},
        {"name": "Performance", "score": 80},
        {"name": "Security", "score": 90},
        {"name": "Complexity", "score": 50},
    ]
    expected = round(0.25 * 90 + 0.20 * 80 + 0.20 * 70 + 0.20 * 60 + 0.15 * 50, 1)
    assert calculate_weighted_score(dims) == expected
