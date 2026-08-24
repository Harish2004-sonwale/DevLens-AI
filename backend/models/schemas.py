"""
DevLens AI — Pydantic schemas for all API request and response models.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Supported languages registry
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = [
    "python",
    "java",
    "c",
    "cpp",
    "javascript",
    "typescript",
    "csharp",
    "go",
]

LANGUAGE_DISPLAY = {
    "python": "Python",
    "java": "Java",
    "c": "C",
    "cpp": "C++",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "csharp": "C#",
    "go": "Go",
    "rust": "Rust",
    "php": "PHP",
    "kotlin": "Kotlin",
    "swift": "Swift",
}

LANGUAGE_EXTENSIONS = {
    "python": "py",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "javascript": "js",
    "typescript": "ts",
    "csharp": "cs",
    "go": "go",
    "rust": "rs",
    "php": "php",
    "kotlin": "kt",
    "swift": "swift",
}

# Framework registry per language
SUPPORTED_FRAMEWORKS = {
    "python": ["pytest", "unittest"],
    "java": ["JUnit"],
    "javascript": ["Jest", "Mocha"],
    "typescript": ["Jest", "Mocha"],
    "cpp": ["GoogleTest", "Catch2"],
    "c": ["Unity"],
    "csharp": ["xUnit", "NUnit"],
    "go": ["testing"],
}

DEFAULT_FRAMEWORKS = {
    "python": "pytest",
    "java": "JUnit",
    "javascript": "Jest",
    "typescript": "Jest",
    "cpp": "GoogleTest",
    "c": "Unity",
    "csharp": "xUnit",
    "go": "testing",
}

# Deterministic weighted quality scoring model
DIMENSION_WEIGHTS = {
    "Security": 0.25,
    "Performance": 0.20,
    "Readability": 0.20,
    "Maintainability": 0.20,
    "Complexity": 0.15,
}

MAX_CODE_LENGTH = 50_000  # characters


# ---------------------------------------------------------------------------
# Shared validators
# ---------------------------------------------------------------------------


def validate_code(v: str) -> str:
    if not v or not v.strip():
        raise ValueError("Source code must not be empty.")
    if len(v) > MAX_CODE_LENGTH:
        raise ValueError(
            f"Source code exceeds maximum allowed length of {MAX_CODE_LENGTH} characters."
        )
    return v.strip()


def validate_language(v: str) -> str:
    normalized = v.lower().strip()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{v}'. Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    return normalized


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TranslateRequest(BaseModel):
    source_code: str = Field(..., description="The source code to translate.")
    source_language: str = Field(..., description="Source programming language.")
    target_language: str = Field(..., description="Target programming language.")
    preserve_comments: bool = Field(True, description="Whether to preserve comments.")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("source_language", "target_language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


class DetectLanguageRequest(BaseModel):
    source_code: str = Field(..., description="Code to analyze for language detection.")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)


class ExplainRequest(BaseModel):
    source_code: str = Field(..., description="The code to explain.")
    language: str = Field(..., description="Programming language of the source code.")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


class DebugRequest(BaseModel):
    source_code: str = Field(..., description="The code to analyze for bugs.")
    language: str = Field(..., description="Programming language of the code.")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


class FixBugsRequest(BaseModel):
    source_code: str = Field(..., description="The buggy source code.")
    language: str = Field(..., description="Programming language of the code.")
    issues_summary: Optional[str] = Field(None, description="Summary of bugs to fix.")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


class OptimizeRequest(BaseModel):
    source_code: str = Field(..., description="The code to optimize.")
    language: str = Field(..., description="Programming language of the code.")
    focus: str = Field("balanced", description="Optimization focus: performance/readability/memory/balanced")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


class GenerateTestsRequest(BaseModel):
    source_code: str = Field(..., description="The code for which to generate tests.")
    language: str = Field(..., description="Programming language of the code.")
    framework: Optional[str] = Field(None, description="Test framework to use (e.g. pytest, unittest, JUnit, Jest).")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


class AnalyzeRequest(BaseModel):
    source_code: str = Field(..., description="The code to analyze for quality.")
    language: str = Field(..., description="Programming language of the code.")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


class ImproveCodeRequest(BaseModel):
    source_code: str = Field(..., description="The code to improve.")
    language: str = Field(..., description="Programming language of the code.")
    recommendations: Optional[List[str]] = Field(default_factory=list, description="Quality recommendations to address.")

    @field_validator("source_code")
    @classmethod
    def check_code(cls, v: str) -> str:
        return validate_code(v)

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        return validate_language(v)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TranslateResponse(BaseModel):
    success: bool
    source_language: str
    target_language: str
    converted_code: str
    explanation: str = ""
    warnings: List[str] = []
    quality_score: Optional[float] = None
    execution_time_ms: Optional[float] = None
    history_id: Optional[int] = None


class DetectionAlternative(BaseModel):
    language: str
    confidence: float


class DetectLanguageResponse(BaseModel):
    success: bool
    detected_language: str
    confidence: float
    display_name: str
    alternatives: List[DetectionAlternative] = []


class ExplainResponse(BaseModel):
    success: bool
    language: str
    overview: str
    detailed_explanation: str
    functions_and_classes: List[str] = []
    important_variables: List[str] = []
    algorithm: str = ""
    time_complexity: str = ""
    space_complexity: str = ""
    potential_issues: List[str] = []
    example_walkthrough: str = ""
    concepts_used: List[str] = []
    edge_cases: List[str] = []
    history_id: Optional[int] = None


class BugItem(BaseModel):
    line_number: Optional[int] = None
    issue: str
    severity: str  # critical / high / medium / low
    explanation: str
    recommendation: Optional[str] = ""
    suggested_fix: str


class DebugResponse(BaseModel):
    success: bool
    language: str
    bugs: List[BugItem] = []
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary: str = ""
    fixed_code: Optional[str] = None
    corrected_code: Optional[str] = None
    history_id: Optional[int] = None


class FixBugsResponse(BaseModel):
    success: bool
    language: str
    original_code: str
    fixed_code: str
    fix_summary: str = ""
    fixed_issues_count: int = 0
    history_id: Optional[int] = None


class OptimizationChange(BaseModel):
    description: str
    reason: str
    category: str  # readability / implementation / performance / memory / maintainability / algorithmic


class OptimizeResponse(BaseModel):
    success: bool
    language: str
    original_code: str
    optimized_code: str
    before_complexity: Optional[str] = None
    after_complexity: Optional[str] = None
    before_time_complexity: Optional[str] = "N/A"
    after_time_complexity: Optional[str] = "N/A"
    before_space_complexity: Optional[str] = "N/A"
    after_space_complexity: Optional[str] = "N/A"
    complexity_summary: Optional[str] = ""
    changes: List[OptimizationChange] = []
    performance_notes: str = ""
    readability_notes: str = ""
    history_id: Optional[int] = None


class TestCase(BaseModel):
    name: str
    description: str
    test_code: str
    expected_output: str = ""
    test_type: str = "normal"  # normal / edge / exception / security / regression
    is_edge_case: bool = False


class GenerateTestsResponse(BaseModel):
    success: bool
    language: str
    test_framework: str
    test_code: str
    test_cases: List[TestCase] = []
    total_count: int = 0
    normal_count: int = 0
    edge_count: int = 0
    exception_count: int = 0
    security_count: int = 0
    regression_count: int = 0
    history_id: Optional[int] = None


class QualityDimension(BaseModel):
    name: str
    score: float
    weight: float = 0.20
    description: str


class AnalyzeResponse(BaseModel):
    success: bool
    language: str
    overall_score: float
    scoring_model: str = "Deterministic Weighted Model (Security 25%, Performance 20%, Readability 20%, Maintainability 20%, Complexity 15%)"
    dimensions: List[QualityDimension] = []
    recommendations: List[str] = []
    summary: str = ""
    history_id: Optional[int] = None


class ImproveCodeResponse(BaseModel):
    success: bool
    language: str
    original_code: str
    improved_code: str
    improvements_applied: List[str] = []
    improvement_summary: str = ""
    history_id: Optional[int] = None


# ---------------------------------------------------------------------------
# History schemas
# ---------------------------------------------------------------------------


class HistoryItem(BaseModel):
    id: int
    source_language: str
    target_language: Optional[str] = None
    source_code: str
    converted_code: Optional[str] = None
    operation: str
    status: str
    quality_score: Optional[float] = None
    explanation: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryListResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    limit: int
    offset: int


class HistoryDetailResponse(BaseModel):
    success: bool
    item: HistoryItem


class HistoryClearResponse(BaseModel):
    success: bool
    deleted_count: int
    message: str


# ---------------------------------------------------------------------------
# Generic error / health
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    gemini_configured: bool
    database_ok: bool
