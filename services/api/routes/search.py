from fastapi import APIRouter, Query
from services.api.db import get_db

router = APIRouter(tags=["Search"])


@router.get("/search")
def search_schemes(q: str = Query(..., min_length=1)):
    with get_db() as cur:
        cur.execute("""
            SELECT s.id, s.name, s.description, s.eligibility_text,
                   s.state_code, s.status, s.source, s.link,
                   s.tags, s.confidence_score,
                   c.name as category_name, p.name as provider_name,
                   ts_rank(
                       to_tsvector('english', COALESCE(s.name, '') || ' ' || COALESCE(s.description, '')),
                       plainto_tsquery('english', %s)
                   ) as rank
            FROM schemes s
            LEFT JOIN categories c ON s.category_id = c.id
            LEFT JOIN providers p ON s.provider_id = p.id
            WHERE to_tsvector('english', COALESCE(s.name, '') || ' ' || COALESCE(s.description, ''))
                  @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT 50
        """, (q, q))
        rows = cur.fetchall()

        if not rows:
            cur.execute("""
                SELECT s.id, s.name, s.description, s.eligibility_text,
                       s.state_code, s.status, s.source, s.link,
                       s.tags, s.confidence_score,
                       c.name as category_name, p.name as provider_name
                FROM schemes s
                LEFT JOIN categories c ON s.category_id = c.id
                LEFT JOIN providers p ON s.provider_id = p.id
                WHERE s.name ILIKE %s OR s.description ILIKE %s
                ORDER BY s.confidence_score DESC NULLS LAST
                LIMIT 50
            """, (f"%{q}%", f"%{q}%"))
            rows = cur.fetchall()

    results = []
    for row in rows:
        results.append({
            "id": str(row["id"]),
            "name": row["name"],
            "description": row["description"],
            "eligibility_text": row["eligibility_text"],
            "state_code": row["state_code"],
            "status": row["status"],
            "source": row["source"],
            "link": row["link"],
            "tags": row["tags"],
            "confidence_score": float(row["confidence_score"]) if row["confidence_score"] else None,
            "category_name": row["category_name"],
            "provider_name": row["provider_name"],
        })

    return {"results": results, "query": q, "total": len(results)}
