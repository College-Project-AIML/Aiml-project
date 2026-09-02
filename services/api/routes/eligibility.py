"""Routes for eligibility checking.
Accepts a user profile and returns matching schemes based on the
eligibility_rules table, ranked by ML-powered personalized relevance.
"""

from fastapi import APIRouter
from services.api.db import get_db
from services.api.models.scheme import EligibilityCheckRequest
from services.api.ml.ranker import rank_schemes

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
        st = req.state.upper()
        conditions.append("(s.state_code IS NULL OR s.state_code IN ('', 'IN') OR s.state_code = %s OR (e.states IS NOT NULL AND %s = ANY(e.states)))")
        params.extend([st, st])

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

    # Collect scheme IDs to fetch eligibility rules
    scheme_ids = [str(row["id"]) for row in rows]
    rules_map = {}
    if scheme_ids:
        placeholders = ", ".join(["%s"] * len(scheme_ids))
        with get_db() as cur2:
            cur2.execute(f"""
                SELECT scheme_id, min_age, max_age, max_income,
                       gender, caste, states, education_level
                FROM eligibility_rules
                WHERE scheme_id IN ({placeholders})
            """, scheme_ids)
            for r in cur2.fetchall():
                rules_map[str(r["scheme_id"])] = {
                    "min_age": r["min_age"],
                    "max_age": r["max_age"],
                    "max_income": float(r["max_income"]) if r["max_income"] else None,
                    "gender": r["gender"],
                    "caste": r["caste"],
                    "states": r["states"],
                    "education_level": r["education_level"],
                }

    # Build user profile dict
    profile = {
        "age": req.age,
        "income": req.income,
        "gender": req.gender,
        "caste": req.caste,
        "state": req.state,
        "education_level": req.education_level,
    }

    # Build schemes-with-rules for the ranker
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
        schemes_with_rules.append({
            "scheme": scheme_dict,
            "rules": rules_map.get(sid),
        })

    # Rank by personalized ML relevance score
    ranked = rank_schemes(profile, schemes_with_rules, limit=50)

    # Build response with match reasons
    matches = []
    for item in ranked:
        match_details = item.get("match_details", {})
        criteria = match_details.get("criteria", [])
        reasons = []
        for c in criteria:
            if c["status"] == "match":
                reasons.append(f"{c['label']}: eligible")
            elif c["status"] == "fail":
                reasons.append(f"{c['label']}: not met")

        matches.append({
            "scheme": {
                "id": item["id"],
                "name": item["name"],
                "description": item["description"],
                "eligibility_text": item["eligibility_text"],
                "state_code": item["state_code"],
                "status": item["status"],
                "source": item["source"],
                "link": item["link"],
                "tags": item["tags"],
                "confidence_score": item.get("relevance_score"),
                "category_name": item["category_name"],
                "provider_name": item["provider_name"],
            },
            "relevance_score": item.get("relevance_score"),
            "match_details": match_details,
            "match_reason": "; ".join(reasons) if reasons else "Open to all / no specific restrictions",
        })

    return {"matches": matches, "total_matches": len(matches)}
