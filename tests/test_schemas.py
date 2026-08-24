import pytest
from pydantic import ValidationError
from backend.models.schemas import (
    TranslateRequest,
    DetectLanguageRequest,
    ExplainRequest,
    DebugRequest,
    OptimizeRequest,
    GenerateTestsRequest,
    AnalyzeRequest,
    ImproveCodeRequest,
    FixBugsRequest,
    DIMENSION_WEIGHTS,
    DEFAULT_FRAMEWORKS,
    SUPPORTED_LANGUAGES,
    validate_code,
    validate_language,
)


def test_validate_language_valid():
    for lang in SUPPORTED_LANGUAGES:
        assert validate_language(lang) == lang
        assert validate_language(lang.upper()) == lang


def test_validate_language_invalid():
    with pytest.raises(ValueError, match="Unsupported language"):
        validate_language("unsupported_lang")


def test_validate_code_empty():
    with pytest.raises(ValueError, match="Source code must not be empty"):
        validate_code("")
    with pytest.raises(ValueError, match="Source code must not be empty"):
        validate_code("   \n\t  ")


def test_validate_code_length_exceeded():
    with pytest.raises(ValueError, match="exceeds maximum"):
        validate_code("a" * 50_001)


def test_translate_request_schema():
    req = TranslateRequest(
        source_code="print('hello')",
        source_language="python",
        target_language="javascript",
        preserve_comments=True,
    )
    assert req.source_language == "python"
    assert req.target_language == "javascript"
    assert req.preserve_comments is True


def test_detect_language_request():
    req = DetectLanguageRequest(source_code="def foo(): pass")
    assert req.source_code == "def foo(): pass"


def test_debug_request():
    req = DebugRequest(source_code="x = 10", language="python")
    assert req.language == "python"


def test_optimize_request():
    req = OptimizeRequest(source_code="x = 10", language="python", focus="performance")
    assert req.focus == "performance"


def test_analyze_request():
    req = AnalyzeRequest(source_code="x = 10", language="python")
    assert req.language == "python"


def test_generate_tests_request():
    req = GenerateTestsRequest(source_code="x = 10", language="python", framework="pytest")
    assert req.language == "python"
    assert req.framework == "pytest"


def test_improve_and_fix_request_schemas():
    improve = ImproveCodeRequest(
        source_code="x = 10", language="python", recommendations=["Add types"]
    )
    assert improve.recommendations == ["Add types"]
    fix = FixBugsRequest(source_code="x = 10", language="python", issues_summary="bug")
    assert fix.issues_summary == "bug"


def test_dimension_weights_sum_to_one():
    assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9
    assert DIMENSION_WEIGHTS["Security"] == 0.25
    assert DEFAULT_FRAMEWORKS["python"] == "pytest"
    assert DEFAULT_FRAMEWORKS["javascript"] == "Jest"
