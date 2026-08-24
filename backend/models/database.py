"""
DevLens AI — Database models, history logging, and session management.
Uses SQLAlchemy with SQLite for reliable local persistence.
"""

import json
import os
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    desc,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Resolve DB path relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)

# Accept a legacy database file for backward compatibility, else use devlens.db.
# DEVLENS_DB_PATH env-var overrides both (used by tests).
_LEGACY_DB_PATH = os.path.join(DB_DIR, "codeforge.db")
NEW_DB = os.path.join(DB_DIR, "devlens.db")
DB_PATH = os.getenv("DEVLENS_DB_PATH") or (
    _LEGACY_DB_PATH if os.path.exists(_LEGACY_DB_PATH) else NEW_DB
)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class ConversionHistory(Base):
    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, index=True)
    source_language = Column(String(50), nullable=False)
    target_language = Column(String(50), nullable=True)
    source_code = Column(Text, nullable=False)
    converted_code = Column(Text, nullable=True)
    operation = Column(String(50), nullable=False, default="translate")
    status = Column(String(20), nullable=False, default="success")
    quality_score = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)  # JSON-encoded list
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_history(
    db: Session,
    source_language: str,
    target_language: Optional[str],
    source_code: str,
    converted_code: Optional[str],
    operation: str,
    status: str = "success",
    quality_score: Optional[float] = None,
    explanation: Optional[str] = None,
    warnings: Optional[List[str]] = None,
) -> ConversionHistory:
    """Helper to log an operation into history."""
    entry = ConversionHistory(
        source_language=source_language,
        target_language=target_language,
        source_code=source_code,
        converted_code=converted_code,
        operation=operation,
        status=status,
        quality_score=quality_score,
        explanation=explanation,
        warnings=json.dumps(warnings) if warnings else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
