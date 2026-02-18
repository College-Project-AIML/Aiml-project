"""
Routes for category listing.
"""

from fastapi import APIRouter
from services.api.db import get_db

router = APIRouter(tags=["Categories"])


@router.get("/categories")
def list_categories():
    with get_db() as cur:
        cur.execute("""
            SELECT c.id, c.name, c.slug, c.description,
                   COUNT(s.id) as scheme_count
            FROM categories c
            LEFT JOIN schemes s ON s.category_id = c.id
            GROUP BY c.id, c.name, c.slug, c.description
            ORDER BY scheme_count DESC, c.name
        """)
        rows = cur.fetchall()

    return [
        {
            "id": str(row["id"]),
            "name": row["name"],
            "slug": row["slug"],
            "description": row["description"],
            "scheme_count": row["scheme_count"],
        }
        for row in rows
    ]
