"""
DevLens AI — FastAPI Application Entry Point.
AI-Powered Developer Intelligence Platform
Tagline: Understand. Improve. Transform. Test.

Run with:
    python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from backend.api import analyze, convert, debug, explain, history, optimize, tests
from backend.models.database import init_db
from backend.utils.security import configure_cors, limiter

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("devlens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DevLens AI starting up...")
    init_db()
    logger.info("Database initialized.")
    yield
    logger.info("DevLens AI shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DevLens AI",
    description=(
        "DevLens AI — AI-Powered Developer Intelligence Platform.\n"
        "Understand. Improve. Transform. Test.\n"
        "Features: Code Converter, Bug Detector with Fix With AI, Code Optimizer, "
        "Code Explainer, Code Analyzer with Deterministic Scoring, Test Generator, and Operation History."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter

# CORS
configure_cors(app)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Rate limit exceeded. Please wait and try again.",
            "detail": "Too many requests.",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if not isinstance(detail, str):
        detail = "Invalid request."
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": detail, "detail": detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
            "detail": "Internal server error",
        },
    )


# ---------------------------------------------------------------------------
# Static files (frontend)
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse("frontend/index.html")


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

API_PREFIX = "/api"

app.include_router(convert.router, prefix=API_PREFIX, tags=["Convert"])
app.include_router(analyze.router, prefix=API_PREFIX, tags=["Analyze"])
app.include_router(debug.router, prefix=API_PREFIX, tags=["Debug"])
app.include_router(explain.router, prefix=API_PREFIX, tags=["Explain"])
app.include_router(optimize.router, prefix=API_PREFIX, tags=["Optimize"])
app.include_router(tests.router, prefix=API_PREFIX, tags=["Tests"])
app.include_router(history.router, prefix=API_PREFIX, tags=["History"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health", tags=["Health"])
async def health():
    """Return DevLens service health status."""
    from backend.models.database import engine
    from backend.services.gemini_service import is_configured
    from sqlalchemy import text

    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "product": "DevLens AI",
        "version": "2.0.0",
        "tagline": "Understand. Improve. Transform. Test.",
        "gemini_configured": is_configured(),
        "database_ok": db_ok,
    }
