"""
features.py — Feature extraction for user-scheme personalization.

Extracts features from a (user_profile, eligibility_rules, scheme) triple
to feed into the ranking scorer.  All features are floats in [0, 1] so the
scorer doesn't need to worry about scales.

User profile keys expected:
    age, income, gender, caste, state, education_level

Eligibility rules keys (from eligibility_rules table):
    min_age, max_age, max_income, gender, caste, states, education_level

Scheme keys:
    state_code, source, confidence_score (source trust)
"""

from __future__ import annotations

from typing import Any, Optional

# ── Education ordinal encoding ──────────────────────────────────────────────
_EDUCATION_ORDINAL = {
    "7th_pass": 1,
    "8th_pass": 2,
    "10th_pass": 3,
    "12th_pass": 4,
    "graduate": 5,
    "post_graduate": 6,
}
_MAX_EDUCATION = 6


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def extract_features(
    profile: dict,
    rules: Optional[dict],
    scheme: dict,
) -> dict[str, float]:
    """
    Build a feature dict for one (user, scheme) pair.

    Parameters
    ----------
    profile : dict
        User profile with keys like age, income, gender, caste, state, education_level.
    rules : dict or None
        Eligibility rules row from the DB (may be None if scheme has no rules).
    scheme : dict
        Scheme row with state_code, source, confidence_score.

    Returns
    -------
    dict[str, float]  — named features, all in roughly [0, 1].
    """
    features: dict[str, float] = {}

    # ── User raw features (normalised) ──────────────────────────────────────
    user_age = _safe_float(profile.get("age"))
    user_income = _safe_float(profile.get("income"))
    user_gender = (profile.get("gender") or "").lower().strip()
    user_caste = (profile.get("caste") or "").upper().strip()
    user_state = (profile.get("state") or "").upper().strip()
    user_edu = (profile.get("education_level") or "").lower().strip()

    features["user_age_norm"] = min(user_age / 100.0, 1.0) if user_age else 0.0
    features["user_income_norm"] = min(user_income / 1_000_000.0, 1.0) if user_income else 0.0
    features["user_edu_norm"] = _EDUCATION_ORDINAL.get(user_edu, 0) / _MAX_EDUCATION

    # ── State Eligibility Evaluation ──────────────────────────────────────
    scheme_state = (scheme.get("state_code") or "").upper().strip()
    rule_states = (rules.get("states") if rules else None) or []
    has_state_restriction = len(rule_states) > 0 or scheme_state not in ("", "IN")
    if user_state and has_state_restriction:
        if scheme_state == user_state or user_state in rule_states:
            features["state_eligible"] = 1.0
        else:
            features["state_eligible"] = 0.0
    elif user_state and rule_states:
        features["state_eligible"] = 1.0 if user_state in rule_states else 0.0
    else:
        features["state_eligible"] = 1.0

    # ── Eligibility cross-features ──────────────────────────────────────────
    if rules is None:
        # No rules table entry → scheme is open to general criteria, except state constraint
        features["age_eligible"] = 1.0
        features["income_eligible"] = 1.0
        features["gender_eligible"] = 1.0
        features["caste_eligible"] = 1.0
        features["education_eligible"] = 1.0
        features["has_any_rule"] = 1.0 if has_state_restriction else 0.0
        features["matched_rule_coverage"] = (1.0 / 6.0) if has_state_restriction and features["state_eligible"] > 0.5 else 0.0
        features["eligibility_match_ratio"] = features["state_eligible"]
    else:
        # ── Age ─────────────────────────────────────────────────────────────
        min_age = _safe_float(rules.get("min_age"))
        max_age = _safe_float(rules.get("max_age"))
        has_age = min_age > 0 or max_age > 0
        if has_age and user_age:
            age_ok = (min_age == 0 or user_age >= min_age) and (max_age == 0 or user_age <= max_age)
            if age_ok:
                features["age_eligible"] = 1.0
            else:
                if min_age > 0 and user_age < min_age:
                    features["age_eligible"] = max(0.0, 1.0 - (min_age - user_age) / 20.0)
                elif max_age > 0 and user_age > max_age:
                    features["age_eligible"] = max(0.0, 1.0 - (user_age - max_age) / 20.0)
                else:
                    features["age_eligible"] = 0.0
        else:
            features["age_eligible"] = 1.0

        # ── Income ──────────────────────────────────────────────────────────
        max_income = _safe_float(rules.get("max_income"))
        has_income = max_income > 0
        if has_income and user_income:
            features["income_eligible"] = 1.0 if user_income <= max_income else 0.0
            if user_income > max_income and max_income > 0:
                overshoot = (user_income - max_income) / max_income
                features["income_eligible"] = max(0.0, 1.0 - overshoot)
        else:
            features["income_eligible"] = 1.0

        # ── Gender ──────────────────────────────────────────────────────────
        rule_gender = rules.get("gender") or []
        has_gender = len(rule_gender) > 0
        if has_gender and user_gender:
            features["gender_eligible"] = 1.0 if user_gender in rule_gender else 0.0
        else:
            features["gender_eligible"] = 1.0

        # ── Caste ───────────────────────────────────────────────────────────
        rule_caste = rules.get("caste") or []
        has_caste = len(rule_caste) > 0
        if has_caste and user_caste:
            features["caste_eligible"] = 1.0 if user_caste in rule_caste else 0.0
        else:
            features["caste_eligible"] = 1.0

        # ── Education ───────────────────────────────────────────────────────
        rule_edu = (rules.get("education_level") or "").lower().strip()
        has_edu = bool(rule_edu)
        if has_edu and user_edu:
            user_ord = _EDUCATION_ORDINAL.get(user_edu, 0)
            rule_ord = _EDUCATION_ORDINAL.get(rule_edu, 0)
            features["education_eligible"] = 1.0 if user_ord >= rule_ord else 0.0
        else:
            features["education_eligible"] = 1.0

        # ── Aggregate ───────────────────────────────────────────────────────
        applicable = sum([has_age, has_income, has_gender, has_caste, has_state_restriction, has_edu])
        # Only count criteria that actually apply to this scheme. Counting
        # unrestricted criteria as passes made the ratio exceed 1.0 (for
        # example, one applicable rule plus five unrestricted fields), which
        # pushed many scores to the same maximum.
        passed = sum([
            has_age and features["age_eligible"] > 0.5,
            has_income and features["income_eligible"] > 0.5,
            has_gender and features["gender_eligible"] > 0.5,
            has_caste and features["caste_eligible"] > 0.5,
            has_state_restriction and features["state_eligible"] > 0.5,
            has_edu and features["education_eligible"] > 0.5,
        ])
        features["eligibility_match_ratio"] = passed / max(applicable, 1)
        features["has_any_rule"] = 1.0 if applicable > 0 else 0.0
        # Prefer schemes that are specifically relevant to this profile over
        # unrestricted schemes which happen to be open to everyone.
        features["matched_rule_coverage"] = sum([
            has_age and features["age_eligible"] > 0.5,
            has_income and features["income_eligible"] > 0.5,
            has_gender and features["gender_eligible"] > 0.5,
            has_caste and features["caste_eligible"] > 0.5,
            has_state_restriction and features["state_eligible"] > 0.5,
            has_edu and features["education_eligible"] > 0.5,
        ]) / 6.0

    # ── Scheme metadata features ────────────────────────────────────────────
    source = (scheme.get("source") or "").lower()
    features["source_trust"] = _source_trust(source)
    features["is_all_india"] = 1.0 if (scheme.get("state_code") or "").upper() == "IN" else 0.0

    return features


def _source_trust(source: str) -> float:
    """Map source domain to a trust score."""
    if not source:
        return 0.3
    if "gov.in" in source or "nic.in" in source:
        return 0.95
    if "scholarships.gov.in" in source:
        return 1.0
    return 0.5


# ── Feature names (for model training / interpretability) ───────────────────
FEATURE_NAMES = [
    "user_age_norm",
    "user_income_norm",
    "user_edu_norm",
    "age_eligible",
    "income_eligible",
    "gender_eligible",
    "caste_eligible",
    "state_eligible",
    "education_eligible",
    "eligibility_match_ratio",
    "has_any_rule",
    "matched_rule_coverage",
    "source_trust",
    "is_all_india",
]
