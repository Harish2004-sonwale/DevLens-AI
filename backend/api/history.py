"""
DevLens AI — /api/history route.
Provides querying, filtering, retrieval, and deletion of past conversion and analysis operations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from backend.models.database import ConversionHistory, get_db
from backend.models.schemas import (
    HistoryClearResponse,
    HistoryDetailResponse,
    HistoryItem,
    HistoryListResponse,
)
from backend.utils.security import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/history",
    response_model=HistoryListResponse,
    summary="Get recent activity history",
)
@limiter.limit("60/minute")
async def get_history(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Records offset for pagination"),
    operation: Optional[str] = Query(None, description="Filter by tool/operation"),
    status: Optional[str] = Query(None, description="Filter by status (success/error)"),
    q: Optional[str] = Query(None, description="Search operation, language, or code"),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    """Retrieve paginated operation history with optional filters."""
    query = db.query(ConversionHistory)

    if operation and operation.lower() != "all":
        query = query.filter(ConversionHistory.operation == operation.lower())

    if status:
        query = query.filter(ConversionHistory.status == status.lower())

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                ConversionHistory.operation.ilike(term),
                ConversionHistory.source_language.ilike(term),
                ConversionHistory.target_language.ilike(term),
                ConversionHistory.explanation.ilike(term),
            )
        )

    total = query.count()
    records = (
        query.order_by(desc(ConversionHistory.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [HistoryItem.model_validate(r) for r in records]

    return HistoryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/history/{history_id}",
    response_model=HistoryDetailResponse,
    summary="Get specific history entry by ID",
)
@limiter.limit("60/minute")
async def get_history_item(
    request: Request,
    history_id: int,
    db: Session = Depends(get_db),
) -> HistoryDetailResponse:
    """Retrieve full details of a specific history record."""
    entry = db.query(ConversionHistory).filter(ConversionHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="History record not found.")

    return HistoryDetailResponse(
        success=True,
        item=HistoryItem.model_validate(entry),
    )


@router.delete(
    "/history/{history_id}",
    summary="Delete a single history record",
)
@limiter.limit("30/minute")
async def delete_history_item(
    request: Request,
    history_id: int,
    db: Session = Depends(get_db),
):
    """Delete a specific record from history."""
    entry = db.query(ConversionHistory).filter(ConversionHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="History record not found.")

    db.delete(entry)
    db.commit()
    return {"success": True, "deleted_id": history_id, "message": "History item deleted."}


@router.delete(
    "/history",
    response_model=HistoryClearResponse,
    summary="Clear all history records",
)
@limiter.limit("10/minute")
async def clear_history(
    request: Request,
    db: Session = Depends(get_db),
) -> HistoryClearResponse:
    """Clear all operations from the history table."""
    deleted_count = db.query(ConversionHistory).delete()
    db.commit()
    return HistoryClearResponse(
        success=True,
        deleted_count=deleted_count,
        message=f"Cleared {deleted_count} history records.",
    )
