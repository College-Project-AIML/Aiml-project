"""
Routes for eligibility checking.
Accepts a user profile and returns matching schemes based on the
eligibility_rules table.
"""

from fastapi import APIRouter
from services.api.db import get_db
from services.api.models.scheme import EligibilityCheckRequest

router = APIRouter(tags=["Eligibility"])


@router.post("/eligibility-check")
def check_eligibility(req: EligibilityCheckRequest):
    conditions = []
    params = []

    if req.age is not None:
        conditions.append("(e.min_age IS NULL OR e.min_age <= %s)")
        params.append(req.age)
        conditions.append("(e.max_age IS NULL OR e.max_age >= %s)")
        params.append(req.age)

    if req.income is not None:
        conditions.append("(e.max_income IS NULL OR e.max_income >= %s)")
        params.append(req.income)

    if req.gender:
        conditions.append("(e.gender IS NULL OR %s = ANY(e.gender))")
        params.append(req.gender.lower())

    if req.caste:
        conditions.append("(e.caste IS NULL OR %s = ANY(e.caste))")
        params.append(req.caste.upper())

    if req.state:
        conditions.append("(e.states IS NULL OR %s = ANY(e.states))")
        params.append(req.state.upper())

    if req.education_level:
        conditions.append("(e.education_level IS NULL OR e.education_level = %s)")
        params.append(req.education_level)

    where = " AND ".join(conditions) if conditions else "TRUE"

    with get_db() as cur:
        cur.execute(f"""
            SELECT DISTINCT s.id, s.name, s.description, s.eligibility_text,
                   s.state_code, s.status, s.source, s.link,
                   s.tags, s.confidence_score,
                   c.name as category_name, p.name as provider_name
            FROM schemes s
            LEFT JOIN categories c ON s.category_id = c.id
            LEFT JOIN providers p ON s.provider_id = p.id
            LEFT JOIN eligibility_rules e ON e.scheme_id = s.id
            WHERE s.status = 'ACTIVE' AND ({where})
            ORDER BY s.confidence_score DESC NULLS LAST
            LIMIT 50
        """, params)
        rows = cur.fetchall()

    matches = []
    for row in rows:
        reasons = []
        if req.age:
            reasons.append(f"Age {req.age} eligible")
        if req.income:
            reasons.append(f"Income ₹{req.income:,.0f} within limit")
        if req.caste:
            reasons.append(f"Category: {req.caste}")
        if req.state:
            reasons.append(f"State: {req.state}")

        matches.append({
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
                "confidence_score": float(row["confidence_score"]) if row["confidence_score"] else None,
                "category_name": row["category_name"],
                "provider_name": row["provider_name"],
            },
            "match_reason": "; ".join(reasons) if reasons else "Open to all / no specific restrictions",
        })

    return {"matches": matches, "total_matches": len(matches)}
