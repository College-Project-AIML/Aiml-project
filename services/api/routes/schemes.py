from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from services.api.db import get_db
from services.api.ml.ranker import rank_schemes

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


class RecommendedRequest(BaseModel):
    age: Optional[int] = None
    income: Optional[float] = None
    gender: Optional[str] = None
    caste: Optional[str] = None
    state: Optional[str] = None
    education_level: Optional[str] = None
    category: Optional[str] = None
    limit: int = 20


@router.post("/schemes/recommended")
def get_recommended_schemes(req: RecommendedRequest):
    """
    Return personalized scheme recommendations ranked by ML relevance score.

    Accepts the user's profile and returns schemes sorted by how well
    they match, with a `relevance_score` (0–1) and `match_details` for each.
    """
    profile = {
        "age": req.age,
        "income": req.income,
        "gender": req.gender,
        "caste": req.caste,
        "state": req.state,
        "education_level": req.education_level,
    }

    with get_db() as cur:
        conditions = ["s.status = 'ACTIVE'"]
        params: list = []

        if req.category:
            conditions.append("c.name ILIKE %s")
            params.append(f"%{req.category}%")

        if req.state:
            st = req.state.upper()
            conditions.append("(s.state_code IS NULL OR s.state_code IN ('', 'IN') OR s.state_code = %s OR (e.states IS NOT NULL AND %s = ANY(e.states)))")
            params.extend([st, st])

        where = " AND ".join(conditions)

        cur.execute(f"""
            SELECT s.id, s.name, s.description, s.eligibility_text,
                   s.state_code, s.status, s.source, s.link,
                   s.tags, s.confidence_score,
                   c.name as category_name, p.name as provider_name,
                   e.min_age, e.max_age, e.max_income,
                   e.gender, e.caste, e.states, e.education_level
            FROM schemes s
            LEFT JOIN categories c ON s.category_id = c.id
            LEFT JOIN providers p ON s.provider_id = p.id
            LEFT JOIN eligibility_rules e ON e.scheme_id = s.id
            WHERE {where}
        """, params)
        rows = cur.fetchall()

    schemes_with_rules = []
    for row in rows:
        sid = str(row["id"])
        scheme_dict = {
            "id": sid,
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
        }
        rules = None
        if any(row.get(k) is not None for k in ["min_age", "max_age", "max_income", "gender", "caste", "states", "education_level"]):
            rules = {
                "min_age": row["min_age"],
                "max_age": row["max_age"],
                "max_income": float(row["max_income"]) if row["max_income"] else None,
                "gender": row["gender"],
                "caste": row["caste"],
                "states": row["states"],
                "education_level": row["education_level"],
            }
        schemes_with_rules.append({
            "scheme": scheme_dict,
            "rules": rules,
        })

    # Rank by personalized relevance
    ranked = rank_schemes(profile, schemes_with_rules, limit=req.limit)

    return {
        "schemes": ranked,
        "total": len(ranked),
        "profile_used": {k: v for k, v in profile.items() if v is not None},
    }


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
