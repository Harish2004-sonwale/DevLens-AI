import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from backend.models.database import init_db

client = TestClient(app)
init_db()

SAMPLE = "def add(a, b):\n    return a + b\n"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["product"] == "DevLens AI"
    assert "gemini_configured" in data
    assert data["database_ok"] is True
    assert "GEMINI" not in str(data).upper() or "API_KEY" not in str(data)


def test_index_html_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "DevLens AI" in response.text
    assert "CodeForge" not in response.text
    assert "Understand. Improve. Transform. Test." in response.text


def test_static_assets_have_no_api_key():
    css = client.get("/static/css/main.css")
    js = client.get("/static/js/api.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "GEMINI_API_KEY" not in css.text
    assert "GEMINI_API_KEY" not in js.text
    assert "--bg-base" in css.text


def test_convert_same_language_bad_request():
    response = client.post(
        "/api/convert",
        json={
            "source_code": "print('hello')",
            "source_language": "python",
            "target_language": "python",
            "preserve_comments": True,
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert "must be different" in str(body.get("detail", body.get("error", "")))


def test_convert_invalid_language():
    response = client.post(
        "/api/convert",
        json={
            "source_code": "print('hello')",
            "source_language": "unsupported",
            "target_language": "python",
            "preserve_comments": True,
        },
    )
    assert response.status_code == 422


def test_detect_language_empty_code():
    response = client.post("/api/detect-language", json={"source_code": "   "})
    assert response.status_code == 422


def test_oversized_code_rejected():
    response = client.post(
        "/api/debug",
        json={"source_code": "a" * 50_001, "language": "python"},
    )
    assert response.status_code == 422


@patch("backend.services.gemini_service._call_gemini")
def test_mocked_convert_success(mock_gemini):
    mock_gemini.return_value = {
        "success": True,
        "converted_code": "console.log('hello');",
        "explanation": "Converted Python print to JS console.log",
        "warnings": [],
        "quality_score": 95,
    }
    response = client.post(
        "/api/convert",
        json={
            "source_code": "print('hello')",
            "source_language": "python",
            "target_language": "javascript",
            "preserve_comments": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["converted_code"] == "console.log('hello');"
    assert data["quality_score"] == 95


@patch("backend.services.gemini_service._call_gemini")
def test_mocked_detect_language_success(mock_gemini):
    mock_gemini.return_value = {
        "detected_language": "python",
        "confidence": 0.98,
        "display_name": "Python",
        "alternatives": [],
    }
    response = client.post(
        "/api/detect-language",
        json={"source_code": "this is not obviously any language xyz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] == "python"
    assert data["confidence"] >= 0.80


@patch("backend.services.gemini_service._call_gemini")
def test_debug_and_fix_with_ai(mock_gemini):
    mock_gemini.return_value = {
        "bugs": [
            {
                "line_number": 2,
                "issue": "Division by zero",
                "severity": "critical",
                "explanation": "n can be zero",
                "recommendation": "Guard the divisor",
                "suggested_fix": "if n == 0: raise ValueError()",
            }
        ],
        "summary": "One critical issue",
    }
    debug_res = client.post("/api/debug", json={"source_code": SAMPLE, "language": "python"})
    assert debug_res.status_code == 200
    body = debug_res.json()
    assert body["total_issues"] == 1
    assert body["critical_count"] == 1

    mock_gemini.return_value = {
        "fixed_code": "def add(a, b):\n    return a + b\n",
        "fix_summary": "No remaining issues",
        "fixed_issues_count": 1,
    }
    fix_res = client.post(
        "/api/debug/fix",
        json={"source_code": SAMPLE, "language": "python", "issues_summary": "div zero"},
    )
    assert fix_res.status_code == 200
    assert "return a + b" in fix_res.json()["fixed_code"]


@patch("backend.services.gemini_service._call_gemini")
def test_analyze_and_improve(mock_gemini):
    mock_gemini.return_value = {
        "dimensions": [
            {"name": "Readability", "score": 70, "description": "ok"},
            {"name": "Maintainability", "score": 60, "description": "ok"},
            {"name": "Performance", "score": 80, "description": "ok"},
            {"name": "Security", "score": 90, "description": "ok"},
            {"name": "Complexity", "score": 50, "description": "ok"},
        ],
        "recommendations": ["Add type hints"],
        "summary": "Decent",
    }
    analyze = client.post("/api/analyze", json={"source_code": SAMPLE, "language": "python"})
    assert analyze.status_code == 200
    score = analyze.json()["overall_score"]
    expected = round(0.25 * 90 + 0.20 * 80 + 0.20 * 70 + 0.20 * 60 + 0.15 * 50, 1)
    assert score == expected

    mock_gemini.return_value = {
        "improved_code": "def add(a: int, b: int) -> int:\n    return a + b\n",
        "improvements_applied": ["Added type hints"],
        "improvement_summary": "Typed",
    }
    improve = client.post(
        "/api/analyze/improve",
        json={"source_code": SAMPLE, "language": "python", "recommendations": ["Add type hints"]},
    )
    assert improve.status_code == 200
    assert "int" in improve.json()["improved_code"]


@patch("backend.services.gemini_service._call_gemini")
def test_optimize_explain_and_tests(mock_gemini):
    mock_gemini.return_value = {
        "optimized_code": SAMPLE,
        "before_time_complexity": "O(n)",
        "after_time_complexity": "O(n)",
        "before_space_complexity": "O(1)",
        "after_space_complexity": "O(1)",
        "complexity_summary": "Implementation efficiency improved",
        "changes": [
            {"description": "Rename", "reason": "Clarity", "category": "readability"}
        ],
        "performance_notes": "Unchanged Big-O",
        "readability_notes": "Clearer names",
    }
    opt = client.post(
        "/api/optimize",
        json={"source_code": SAMPLE, "language": "python", "focus": "readability"},
    )
    assert opt.status_code == 200
    assert opt.json()["before_time_complexity"] == "O(n)"
    assert opt.json()["after_time_complexity"] == "O(n)"

    mock_gemini.return_value = {
        "overview": "Adds two numbers",
        "detailed_explanation": "Returns a+b",
        "functions_and_classes": ["add"],
        "important_variables": ["a", "b"],
        "algorithm": "Arithmetic",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
        "potential_issues": [],
        "example_walkthrough": "add(1,2) -> 3",
        "concepts_used": ["functions"],
        "edge_cases": ["overflow"],
    }
    expl = client.post("/api/explain", json={"source_code": SAMPLE, "language": "python"})
    assert expl.status_code == 200
    assert expl.json()["example_walkthrough"]

    mock_gemini.return_value = {
        "test_framework": "pytest",
        "test_code": "def test_add():\n    assert add(1,2)==3\n",
        "test_cases": [
            {"name": "test_add", "description": "happy", "test_code": "assert add(1,2)==3", "expected_output": "pass", "test_type": "normal"},
            {"name": "test_empty", "description": "edge", "test_code": "assert add(0,0)==0", "expected_output": "pass", "test_type": "edge"},
            {"name": "test_type", "description": "err", "test_code": "with pytest.raises(TypeError): add('a',1)", "expected_output": "err", "test_type": "exception"},
        ],
    }
    tests = client.post(
        "/api/generate-tests",
        json={"source_code": SAMPLE, "language": "python", "framework": "pytest"},
    )
    assert tests.status_code == 200
    body = tests.json()
    assert body["test_framework"] == "pytest"
    assert body["normal_count"] == 1
    assert body["edge_count"] == 1
    assert body["exception_count"] == 1


@patch("backend.services.gemini_service._call_gemini")
def test_gemini_failure_is_sanitized(mock_gemini):
    mock_gemini.side_effect = RuntimeError(
        "Gemini API is currently unavailable. Please try again shortly."
    )
    response = client.post("/api/debug", json={"source_code": SAMPLE, "language": "python"})
    assert response.status_code == 502
    detail = str(response.json())
    assert "Traceback" not in detail
    assert "unavailable" in detail.lower()


@patch("backend.services.gemini_service._call_gemini")
def test_malformed_gemini_response(mock_gemini):
    mock_gemini.return_value = {"not": "valid"}
    response = client.post("/api/debug", json={"source_code": SAMPLE, "language": "python"})
    assert response.status_code == 422


def test_history_lifecycle():
    listed = client.get("/api/history?limit=5")
    assert listed.status_code == 200
    assert "items" in listed.json()

    with patch("backend.services.gemini_service._call_gemini") as mock_gemini:
        mock_gemini.return_value = {
            "overview": "x",
            "detailed_explanation": "y",
            "example_walkthrough": "",
            "concepts_used": [],
            "edge_cases": [],
        }
        created = client.post("/api/explain", json={"source_code": SAMPLE, "language": "python"})
    hid = created.json()["history_id"]
    item = client.get(f"/api/history/{hid}")
    assert item.status_code == 200
    assert item.json()["item"]["source_code"] == SAMPLE.strip()

    missing = client.get("/api/history/999999")
    assert missing.status_code == 404

    deleted = client.delete(f"/api/history/{hid}")
    assert deleted.status_code == 200

    cleared = client.delete("/api/history")
    assert cleared.status_code == 200
    assert cleared.json()["success"] is True
