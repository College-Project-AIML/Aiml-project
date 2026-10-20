"""
Event tracking endpoints for ML training data collection.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from services.api.db import get_db
from services.api.auth import get_current_user

router = APIRouter(prefix="/events", tags=["Events"])


class EventMetadata(BaseModel):
    position: Optional[int] = None
    source: Optional[str] = None  # 'recommended', 'matched', 'search', 'category', 'alert'
    dwell_ms: Optional[int] = None
    query: Optional[str] = None
    filter_state: Optional[Dict[str, Any]] = None
    referrer: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class EventRequest(BaseModel):
    event_type: str = Field(..., pattern="^(view|click|apply_start|apply_complete|bookmark|share|search|filter)$")
    scheme_id: Optional[str] = None
    metadata: EventMetadata = Field(default_factory=EventMetadata)
    session_id: Optional[str] = None


class BatchEventRequest(BaseModel):
    events: List[EventRequest]


@router.post("", status_code=201)
async def track_event(
    event: EventRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Record a single user interaction event."""
    user_id = current_user.get("user_id") or current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Generate session_id if not provided
    session_id = event.session_id
    if not session_id:
        session_id = request.cookies.get("session_id") or str(uuid.uuid4())

    with get_db() as cur:
        cur.execute("""
            INSERT INTO user_events (user_id, scheme_id, event_type, metadata, session_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            event.scheme_id,
            event.event_type,
            event.metadata.model_dump_json(),
            session_id,
        ))

    return {"status": "recorded", "session_id": session_id}


@router.post("/batch", status_code=201)
async def track_events_batch(
    batch: BatchEventRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Record multiple events in one request (for buffering)."""
    user_id = current_user.get("user_id") or current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    session_id = batch.events[0].session_id if batch.events else None
    if not session_id:
        session_id = request.cookies.get("session_id") or str(uuid.uuid4())

    with get_db() as cur:
        for event in batch.events:
            cur.execute("""
                INSERT INTO user_events (user_id, scheme_id, event_type, metadata, session_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                event.scheme_id,
                event.event_type,
                event.metadata.model_dump_json(),
                session_id,
            ))

    return {"status": "recorded", "count": len(batch.events), "session_id": session_id}


@router.get("/my-stats")
async def get_my_interaction_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get current user's interaction statistics."""
    user_id = current_user.get("user_id") or current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    with get_db() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'view') as views,
                COUNT(*) FILTER (WHERE event_type = 'click') as clicks,
                COUNT(*) FILTER (WHERE event_type = 'apply_start') as apply_starts,
                COUNT(*) FILTER (WHERE event_type = 'apply_complete') as applications,
                COUNT(*) FILTER (WHERE event_type = 'bookmark') as bookmarks,
                AVG((metadata->>'dwell_ms')::int) FILTER (WHERE metadata->>'dwell_ms' IS NOT NULL) as avg_dwell_ms
            FROM user_events
            WHERE user_id = %s
        """, (user_id,))
        row = cur.fetchone()

        cur.execute("""
            SELECT event_type, COUNT(*) as count
            FROM user_events
            WHERE user_id = %s
            GROUP BY event_type
            ORDER BY count DESC
        """, (user_id,))
        by_type = [{"event_type": r["event_type"], "count": r["count"]} for r in cur.fetchall()]

    return {
        "views": row["views"] or 0,
        "clicks": row["clicks"] or 0,
        "apply_starts": row["apply_starts"] or 0,
        "applications": row["applications"] or 0,
        "bookmarks": row["bookmarks"] or 0,
        "avg_dwell_ms": int(row["avg_dwell_ms"] or 0),
        "by_type": by_type,
    }


# Admin endpoint for ML team
@router.get("/training-data")
async def get_training_data(
    limit: int = 10000,
    offset: int = 0,
    label: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """Export training data for ML model (admin only)."""
    # Check admin role
    roles = current_user.get("https://aiml-project/roles", [])
    if "admin" not in roles and "ml_engineer" not in roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    with get_db() as cur:
        query = "SELECT * FROM ml_training_data"
        params = []
        if label is not None:
            query += " WHERE label = %s"
            params.append(label)
        query += " ORDER BY event_time DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cur.execute(query, params)
        rows = cur.fetchall()

    return {"data": rows, "count": len(rows)}


@router.post("/refresh-training-view")
async def refresh_training_view(
    current_user: dict = Depends(get_current_user),
):
    """Refresh the ML training materialized view (admin only)."""
    roles = current_user.get("https://aiml-project/roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    with get_db() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY ml_training_data")

    return {"status": "refreshed"}