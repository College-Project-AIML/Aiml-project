"""
Lightweight platform statistics for the frontend hero / dashboards.

    GET /api/v1/stats
        -> { total_schemes, total_categories, total_states }
"""

from fastapi import APIRouter

from services.api.db import get_db

router = APIRouter(tags=["Stats"])


@router.get("/stats")
def get_stats():
    with get_db() as cur:
        cur.execute(
            "SELECT COUNT(*) AS total FROM schemes WHERE status = 'ACTIVE'"
        )
        total_schemes = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM categories")
        total_categories = cur.fetchone()["total"]

        cur.execute(
            "SELECT COUNT(DISTINCT state_code) AS total "
            "FROM schemes WHERE state_code IS NOT NULL AND state_code <> ''"
        )
        total_states = cur.fetchone()["total"] or 0

    return {
        "total_schemes": total_schemes,
        "total_categories": total_categories,
        "total_states": total_states,
    }
