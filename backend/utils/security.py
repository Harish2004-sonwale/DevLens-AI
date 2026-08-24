"""
DevLens AI — Security utilities: CORS setup, input sanitization, rate limiting, and safe logging.
"""

import logging
import re
from typing import Dict

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",   # Live Server (VS Code)
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "null",                    # file:// origin (browser direct open)
]


def configure_cors(app) -> None:
    """Attach CORSMiddleware to a FastAPI application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


# ---------------------------------------------------------------------------
# Input sanitization helpers
# ---------------------------------------------------------------------------

# Characters that are safe in code — everything printable + newlines + tabs
_SAFE_CODE_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_code_input(code: str) -> str:
    """Remove control characters that are not valid in source code."""
    return _SAFE_CODE_PATTERN.sub("", code)


def strip_dangerous_headers(headers: dict) -> dict:
    """Return headers with sensitive fields removed (for logging)."""
    sensitive = {"authorization", "x-api-key", "cookie", "gemini_api_key"}
    return {k: v for k, v in headers.items() if k.lower() not in sensitive}


def safe_log_request(request: Request) -> dict:
    """Produce a safe loggable summary of an incoming request."""
    return {
        "method": request.method,
        "path": str(request.url.path),
        "client": request.client.host if request.client else "unknown",
        "headers": strip_dangerous_headers(dict(request.headers)),
    }
