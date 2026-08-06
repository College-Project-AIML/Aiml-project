"""
Routes for the "What's New" updates feed (docs/next.md §3.1).

Exposes the ``scheme_updates`` rows emitted by the live-sync pipeline:

    GET /api/v1/updates?change_type=NEW|UPDATED|CLOSED&since=<iso>&limit=50
        -> { updates: [ { scheme: {...}, change_type, changed_fields, detected_at } ], total }
"""

from typing import Optional

from fastapi import APIRouter, Query

from services.api.db import get_db
from services.api.models.scheme import SchemeUpdateResponse, UpdatesListResponse

router = APIRouter(tags=["Updates"])


@router.get("/updates", response_model=UpdatesListResponse)
def list_updates(
    change_type: Optional[str] = Query(None, description="Filter by NEW | UPDATED | CLOSED"),
    since: Optional[str] = Query(None, description="Only updates detected after this ISO timestamp"),
    limit: int = Query(50, ge=1, le=200),
):
    conditions = []
    params = []

    if change_type:
        conditions.append("u.change_type = %s")
        params.append(change_type.upper())
    if since:
        conditions.append("u.detected_at >= %s")
        params.append(since)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    with get_db() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS total FROM scheme_updates u {where}",
            params,
        )
        total = cur.fetchone()["total"]

        cur.execute(
            f"""
            SELECT u.change_type, u.changed_fields, u.detected_at,
                   s.id, s.name, s.description, s.eligibility_text,
                   s.state_code, s.status, s.source, s.link,
                   s.tags, s.confidence_score,
                   c.name AS category_name, p.name AS provider_name
            FROM scheme_updates u
            JOIN schemes s ON s.id = u.scheme_id
            LEFT JOIN categories c ON s.category_id = c.id
            LEFT JOIN providers p ON s.provider_id = p.id
            {where}
            ORDER BY u.detected_at DESC
            LIMIT %s
            """,
            params + [limit],
        )
        rows = cur.fetchall()

    updates = []
    for row in rows:
        updates.append(
            {
                "change_type": row["change_type"],
                "changed_fields": row["changed_fields"],
                "detected_at": row["detected_at"].isoformat()
                if row["detected_at"]
                else None,
                "scheme": {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "description": row["description"],
                    "eligibility_text": row["eligibility_text"],
                    "state_code": row["state_code"],
                    "status": row["status"],
                    "source": row["source"],
                    "link": row["link"],
                    "tags": row["tags"],
                    "confidence_score": float(row["confidence_score"])
                    if row["confidence_score"]
                    else None,
                    "category_name": row["category_name"],
                    "provider_name": row["provider_name"],
                },
            }
        )

    return {"updates": updates, "total": total}
