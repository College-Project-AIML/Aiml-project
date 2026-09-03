from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.api.db import get_db

router = APIRouter(tags=["Schemes"])


def _scheme_from_row(row):
    """Shape a schemes-table row into the API response object."""
    return {
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
        "last_updated": row["updated_at"].isoformat() if row.get("updated_at") else None,
        "is_new": bool(row.get("is_new")),
    }


def _latest_update(cur, scheme_id):
    """Return the most recent scheme_updates row for a scheme, or None."""
    cur.execute(
        """
        SELECT change_type, changed_fields, detected_at
        FROM scheme_updates
        WHERE scheme_id = %s
        ORDER BY detected_at DESC
        LIMIT 1
        """,
        (scheme_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "change_type": row["change_type"],
        "changed_fields": row["changed_fields"],
        "detected_at": row["detected_at"].isoformat() if row["detected_at"] else None,
    }


@router.get("/schemes")
def list_schemes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, description="recently_updated to order by last sync"),
):
    offset = (page - 1) * limit
    conditions = []
    params = []

    if status:
        conditions.append("s.status = %s")
        params.append(status)
    if category:
        conditions.append("c.name ILIKE %s")
        params.append(f"%{category}%")
    if state:
        conditions.append("(s.state_code = %s OR s.state_code IS NULL)")
        params.append(state.upper())

    order_by = "ORDER BY s.confidence_score DESC NULLS LAST, s.name"
    if sort == "recently_updated":
        order_by = "ORDER BY s.updated_at DESC NULLS LAST, s.name"

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    with get_db() as cur:
        cur.execute(f"""
            SELECT COUNT(*) as total FROM schemes s
            LEFT JOIN categories c ON s.category_id = c.id
            {where}
        """, params)
        total = cur.fetchone()["total"]

        cur.execute(f"""
            SELECT s.id, s.name, s.description, s.eligibility_text,
                   s.state_code, s.status, s.source, s.link,
                   s.tags, s.confidence_score, s.updated_at,
                   c.name as category_name, p.name as provider_name,
                   EXISTS (
                       SELECT 1 FROM scheme_updates u
                       WHERE u.scheme_id = s.id
                         AND u.change_type = 'NEW'
                         AND u.detected_at >= NOW() - INTERVAL '7 days'
                   ) as is_new
            FROM schemes s
            LEFT JOIN categories c ON s.category_id = c.id
            LEFT JOIN providers p ON s.provider_id = p.id
            {where}
            {order_by}
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cur.fetchall()

    schemes = [_scheme_from_row(row) for row in rows]

    return {"schemes": schemes, "total": total, "page": page, "limit": limit}


@router.get("/schemes/{scheme_id}")
def get_scheme(scheme_id: str):
    with get_db() as cur:
        cur.execute("""
            SELECT s.id, s.name, s.description, s.eligibility_text,
                   s.state_code, s.status, s.source, s.link,
                   s.tags, s.confidence_score, s.updated_at,
                   c.name as category_name, p.name as provider_name,
                   EXISTS (
                       SELECT 1 FROM scheme_updates u
                       WHERE u.scheme_id = s.id
                         AND u.change_type = 'NEW'
                         AND u.detected_at >= NOW() - INTERVAL '7 days'
                   ) as is_new
            FROM schemes s
            LEFT JOIN categories c ON s.category_id = c.id
            LEFT JOIN providers p ON s.provider_id = p.id
            WHERE s.id = %s
        """, (scheme_id,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Scheme not found")

        cur.execute("""
            SELECT min_age, max_age, max_income, gender, caste, states, education_level
            FROM eligibility_rules WHERE scheme_id = %s
        """, (scheme_id,))
        rules = cur.fetchall()

        cur.execute("""
            SELECT benefit_type, description, amount, frequency
            FROM benefits WHERE scheme_id = %s
        """, (scheme_id,))
        benefits = cur.fetchall()

        cur.execute("""
            SELECT document_name, is_mandatory
            FROM documents_required WHERE scheme_id = %s
        """, (scheme_id,))
        documents = cur.fetchall()

        latest_update = _latest_update(cur, scheme_id)

    scheme = _scheme_from_row(row)
    scheme["latest_update"] = latest_update
    scheme["eligibility_rules"] = [
        {
            "min_age": r["min_age"],
            "max_age": r["max_age"],
            "max_income": float(r["max_income"]) if r["max_income"] else None,
            "gender": r["gender"],
            "caste": r["caste"],
            "states": r["states"],
            "education_level": r["education_level"],
        }
        for r in rules
    ]
    scheme["benefits"] = [
        {
            "benefit_type": b["benefit_type"],
            "description": b["description"],
            "amount": float(b["amount"]) if b["amount"] else None,
            "frequency": b["frequency"],
        }
        for b in benefits
    ]
    scheme["documents_required"] = [
        {"document_name": d["document_name"], "is_mandatory": d["is_mandatory"]}
        for d in documents
    ]

    return scheme
