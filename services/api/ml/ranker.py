"""
ranker.py — Personalized scheme ranking engine.

Ties together feature extraction and scoring to produce a ranked list
of schemes tailored to a specific user profile.

Usage:
    from services.api.ml.ranker import rank_schemes
    ranked = rank_schemes(profile, schemes_with_rules, limit=20)
"""

from __future__ import annotations

from typing import Optional

from services.api.ml.features import extract_features
from services.api.ml.scorer import score, score_batch


def rank_schemes(
    profile: dict,
    schemes_with_rules: list[dict],
    limit: Optional[int] = 20,
) -> list[dict]:
    """
    Rank a list of schemes by personalized relevance to the user.

    Parameters
    ----------
    profile : dict
        User profile (age, income, gender, caste, state, education_level).
    schemes_with_rules : list[dict]
        Each dict must have:
            - scheme info keys (id, name, description, state_code, source, etc.)
            - "rules" key: dict of eligibility rules (or None)
    limit : int
        Max number of results to return.

    Returns
    -------
    list[dict] — schemes sorted by relevance_score descending, with
    'relevance_score' and 'match_details' added to each scheme dict.
    """
    if not schemes_with_rules:
        return []

    features_list = []
    metadata = []
    for item in schemes_with_rules:
        scheme = item.get("scheme", item)
        rules = item.get("rules")
        feats = extract_features(profile, rules, scheme)
        features_list.append(feats)
        metadata.append((scheme, rules, feats))

    scores = score_batch(features_list)

    scored = []
    for (scheme, rules, feats), relevance in zip(metadata, scores):
        match_details = _build_match_details(feats, rules)
        scored.append({
            **scheme,
            "relevance_score": round(relevance, 4),
            "match_details": match_details,
        })

    # Sort by relevance descending, then by source trust as tiebreaker
    scored.sort(key=lambda s: (s["relevance_score"], float(s.get("confidence_score") or 0)), reverse=True)

    return scored if limit is None else scored[:limit]


def _build_match_details(features: dict[str, float], rules: Optional[dict]) -> dict:
    """
    Create human-readable match details for the frontend.
    """
    details = {
        "eligible": features.get("eligibility_match_ratio", 1.0) > 0.5,
        "match_ratio": round(features.get("eligibility_match_ratio", 1.0), 2),
        "criteria": [],
    }

    if rules is None:
        details["criteria"].append({"field": "all", "status": "open", "label": "Open to all"})
        return details

    criteria_map = [
        ("age_eligible", "age", "Age"),
        ("income_eligible", "income", "Income"),
        ("gender_eligible", "gender", "Gender"),
        ("caste_eligible", "caste", "Category"),
        ("state_eligible", "state", "State"),
        ("education_eligible", "education", "Education"),
    ]

    for feat_key, field, label in criteria_map:
        val = features.get(feat_key, 1.0)
        if val > 0.5:
            status = "match"
            if field in ("age", "income") and val == 1.0:
                # Check if rule actually existed
                rule_key = f"min_{field}" if field == "age" else f"max_{field}"
                if rules.get(rule_key) or rules.get(field == "age" and "max_age" in rules and "min_age" in rules):
                    status = "match"
                else:
                    status = "no_rule"
            elif val == 1.0 and not rules.get(field) and not rules.get(f"{field}s"):
                status = "no_rule"
        else:
            status = "fail"

        details["criteria"].append({
            "field": field,
            "status": status,
            "label": label,
        })

    return details
