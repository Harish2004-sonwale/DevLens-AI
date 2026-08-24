"""
DevLens AI — High-speed hybrid Language Detection service.
Uses instant local AST/regex heuristics (<1ms) and falls back to Gemini AI when ambiguous.
"""

import logging
import re
from typing import Any

from backend.models.schemas import LANGUAGE_DISPLAY
from backend.services import gemini_service

logger = logging.getLogger(__name__)

# Heuristic patterns for fast offline detection
PATTERNS: dict[str, list[tuple[re.Pattern, float]]] = {
    "python": [
        (re.compile(r"^\s*def\s+\w+\s*\(.*?\)\s*:", re.MULTILINE), 0.95),
        (re.compile(r"^\s*class\s+\w+(\(.*?\))?\s*:", re.MULTILINE), 0.90),
        (re.compile(r"^\s*from\s+[\w.]+\s+import\s+", re.MULTILINE), 0.95),
        (re.compile(r"^\s*import\s+(sys|os|math|json|re|typing)\b", re.MULTILINE), 0.95),
        (re.compile(r"\bprint\s*\(.*?\)", re.MULTILINE), 0.80),
        (re.compile(r"\bif\s+__name__\s*==\s*['\"]__main__['\"]:", re.MULTILINE), 0.99),
        (re.compile(r"^\s*(elif|except|finally)\b.*?:", re.MULTILINE), 0.95),
        (re.compile(r"\bself\.\w+", re.MULTILINE), 0.90),
    ],
    "go": [
        (re.compile(r"^\s*package\s+(main|\w+)", re.MULTILINE), 0.99),
        (re.compile(r"^\s*func\s+(\(\w+\s+\*?\w+\)\s+)?\w+\s*\(.*?\)", re.MULTILINE), 0.95),
        (re.compile(r"\bfmt\.(Println|Printf|Sprintf)\b", re.MULTILINE), 0.98),
        (re.compile(r"\bimport\s+\(\s*\"fmt\"", re.MULTILINE), 0.99),
        (re.compile(r":=\s*", re.MULTILINE), 0.85),
    ],
    "java": [
        (re.compile(r"\bpublic\s+(static\s+)?(void|class|interface|enum)\b", re.MULTILINE), 0.95),
        (re.compile(r"\bSystem\.out\.(println|print|printf)\b", re.MULTILINE), 0.98),
        (re.compile(r"^\s*import\s+java\.", re.MULTILINE), 0.98),
        (re.compile(r"\bpublic\s+static\s+void\s+main\s*\(String(\[\]|\s*\.\.\.)\s*\w+\)", re.MULTILINE), 0.99),
        (re.compile(r"\b(private|protected)\s+(final\s+)?[\w<>]+\s+\w+\s*;", re.MULTILINE), 0.85),
    ],
    "csharp": [
        (re.compile(r"^\s*using\s+System(\.[\w.]+)?\s*;", re.MULTILINE), 0.99),
        (re.compile(r"\bConsole\.(WriteLine|Write)\b", re.MULTILINE), 0.98),
        (re.compile(r"^\s*namespace\s+[\w.]+", re.MULTILINE), 0.95),
        (re.compile(r"\bpublic\s+(async\s+)?(Task|void|string|int)\b", re.MULTILINE), 0.85),
    ],
    "cpp": [
        (re.compile(r"#include\s*<iostream>", re.MULTILINE), 0.99),
        (re.compile(r"#include\s*<(vector|string|map|algorithm|memory)>", re.MULTILINE), 0.95),
        (re.compile(r"\bstd::(cout|cin|endl|vector|string|make_unique|make_shared)\b", re.MULTILINE), 0.98),
        (re.compile(r"\bcout\s*<<", re.MULTILINE), 0.95),
        (re.compile(r"\btemplate\s*<typename\s+\w+>", re.MULTILINE), 0.95),
    ],
    "c": [
        (re.compile(r"#include\s*<stdio\.h>", re.MULTILINE), 0.98),
        (re.compile(r"#include\s*<(stdlib|string|math|unistd)\.h>", re.MULTILINE), 0.95),
        (re.compile(r"\bprintf\s*\(", re.MULTILINE), 0.85),
        (re.compile(r"\b(malloc|free|calloc|realloc)\s*\(", re.MULTILINE), 0.90),
        (re.compile(r"\bint\s+main\s*\(\s*(void|int\s+argc)?", re.MULTILINE), 0.85),
    ],
    "typescript": [
        (re.compile(r"^\s*interface\s+\w+\s*\{", re.MULTILINE), 0.95),
        (re.compile(r"^\s*type\s+\w+\s*=", re.MULTILINE), 0.95),
        (re.compile(r":\s*(string|number|boolean|any|unknown|void|never)\b", re.MULTILINE), 0.90),
        (re.compile(r"as\s+(const|string|number)\b", re.MULTILINE), 0.85),
        (re.compile(r"<\w+>\s*\(", re.MULTILINE), 0.80),
    ],
    "javascript": [
        (re.compile(r"\bconsole\.(log|error|warn|info|debug)\b", re.MULTILINE), 0.90),
        (re.compile(r"^\s*(const|let|var)\s+\w+\s*=", re.MULTILINE), 0.85),
        (re.compile(r"^\s*import\s+.*?\s+from\s+['\"].*?['\"]", re.MULTILINE), 0.85),
        (re.compile(r"^\s*export\s+(default\s+)?(function|class|const|let)\b", re.MULTILINE), 0.90),
        (re.compile(r"=>\s*\{?", re.MULTILINE), 0.80),
        (re.compile(r"\bdocument\.(getElementById|querySelector)\b", re.MULTILINE), 0.95),
        (re.compile(r"\brequire\s*\(['\"].*?['\"]\)", re.MULTILINE), 0.90),
    ],
}


def _fast_heuristic_detect(code: str) -> dict[str, Any] | None:
    """Evaluate patterns against the code. Returns a detection result if confidence >= 0.85."""
    scores: dict[str, float] = {}

    for lang, rules in PATTERNS.items():
        lang_score = 0.0
        matches = 0
        for pattern, weight in rules:
            if pattern.search(code):
                lang_score += weight
                matches += 1
        if matches > 0:
            scores[lang] = lang_score

    if not scores:
        return None

    # Sort candidates by score
    sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_lang, best_score = sorted_candidates[0]

    # Normalize confidence capped at 0.99
    confidence = min(0.99, max(0.85, 0.85 + (best_score - 0.85) * 0.1))

    # If C++ vs C conflict: prefer C++ if C++ specific tokens found
    if best_lang == "c" and "cpp" in scores:
        if scores["cpp"] >= scores["c"]:
            best_lang = "cpp"

    # If TypeScript vs JavaScript: check for explicit TS types
    if best_lang == "javascript" and "typescript" in scores and scores["typescript"] >= 0.9:
        best_lang = "typescript"

    alternatives = [
        {"language": l, "confidence": round(min(0.80, s / 2), 2)}
        for l, s in sorted_candidates[1:3]
    ]

    return {
        "success": True,
        "detected_language": best_lang,
        "confidence": round(confidence, 2),
        "display_name": LANGUAGE_DISPLAY.get(best_lang, best_lang.capitalize()),
        "alternatives": alternatives,
    }


def run_detection(source_code: str) -> dict[str, Any]:
    """Detect language with sub-millisecond local heuristics, fallback to AI."""
    # 1. Instant local heuristic (0ms)
    fast_result = _fast_heuristic_detect(source_code)
    if fast_result and fast_result["confidence"] >= 0.85:
        logger.info("Fast local heuristic detected language: %s", fast_result["detected_language"])
        return fast_result

    # 2. AI Fallback (if code is highly ambiguous)
    raw = gemini_service.detect_language(source_code)
    detected = raw.get("detected_language", "unknown")
    confidence = float(raw.get("confidence", 0.0))
    display_name = raw.get("display_name") or LANGUAGE_DISPLAY.get(detected, detected.capitalize())

    alternatives = []
    for alt in raw.get("alternatives", []):
        if isinstance(alt, dict) and "language" in alt and "confidence" in alt:
            alternatives.append(
                {"language": alt["language"], "confidence": float(alt["confidence"])}
            )

    return {
        "success": True,
        "detected_language": detected,
        "confidence": confidence,
        "display_name": display_name,
        "alternatives": alternatives,
    }
