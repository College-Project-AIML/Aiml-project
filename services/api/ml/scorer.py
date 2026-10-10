"""
scorer.py — Personalized relevance scoring for government schemes.

Two modes:
1. ML (default when a model artifact is present):
   XGBoost or LightGBM model trained on user-scheme feature examples.
2. HEURISTIC fallback when no supported model can be loaded.

Both modes accept the same feature dict from features.py and return a
score in [0, 1].
"""

from __future__ import annotations

import os
import json
from typing import Optional

from services.api.ml.features import FEATURE_NAMES

# ── Heuristic weights (tuned for government scheme relevance) ────────────────
# These weights were designed to make eligibility the dominant factor,
# with state/caste match as strong secondary signals.
HEURISTIC_WEIGHTS = {
    "eligibility_match_ratio": 0.30,   # Most important: how many rules the user passes
    "matched_rule_coverage":    0.25,   # Boost schemes with rules that specifically fit this user
    "state_eligible":           0.15,   # State match is critical for state-specific schemes
    "caste_eligible":           0.12,   # Category match matters for reserved schemes
    "income_eligible":          0.08,   # Income threshold
    "age_eligible":             0.05,   # Age range
    "education_eligible":       0.03,   # Education requirement
    "gender_eligible":          0.01,   # Gender (less commonly restricted)
    "source_trust":             0.01,   # Source credibility (minor boost for gov.in)

    # Penalty terms (negative weights for disqualifying mismatches)
    # Applied as: if feature == 0 and it's a hard rule, apply penalty
}

# Hard-qualify threshold: if any of these are 0, the scheme is demoted heavily
_HARD_RULES = {"state_eligible", "caste_eligible", "income_eligible"}

# Penalty for failing a hard rule (subtracted from score)
_HARD_FAIL_PENALTY = 0.40


def score_heuristic(features: dict[str, float]) -> float:
    """
    Compute a personalized relevance score from extracted features.

    Returns a float in [0, 1] where 1 = perfect match.
    """
    # Relevance is primarily an eligibility fit measure. The earlier weighted
    # sum gave unrestricted fields full points, making unrelated profiles
    # look like near-perfect matches. These two features are normalized over
    # applicable rules, so failures and specific matches affect the result.
    match_ratio = features.get("eligibility_match_ratio", 0.0)
    rule_coverage = features.get("matched_rule_coverage", 0.0)
    score = (0.80 * match_ratio) + (0.20 * rule_coverage)
    return max(0.0, min(1.0, score))


# ── ML model support (loads XGBoost/LightGBM if available) ──────────────────

_model = None
_model_type: Optional[str] = None


def _load_ml_model():
    """Attempt to load a trained model from disk."""
    global _model, _model_type

    model_path = os.getenv("RANKER_MODEL_PATH", "models/ranker.json")

    # Resolve relative paths from the project root
    if not os.path.isabs(model_path):
        # Walk up from this file to find the project root (where .env lives)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        model_path = os.path.join(project_root, model_path)

    if not os.path.exists(model_path):
        return

    try:
        # Try XGBoost first
        import xgboost as xgb  # type: ignore
        _model = xgb.Booster()
        _model.load_model(model_path)
        _model_type = "xgboost"
        return
    except (ImportError, Exception):
        pass

    try:
        # Try LightGBM
        import lightgbm as lgb  # type: ignore
        _model = lgb.Booster(model_file=model_path)
        _model_type = "lightgbm"
        return
    except (ImportError, Exception):
        pass

    try:
        # Try pickle (sklearn, etc.)
        import pickle
        with open(model_path, "rb") as f:
            _model = pickle.load(f)
        _model_type = "pickle"
        return
    except Exception:
        pass


def score_ml(features: dict[str, float]) -> Optional[float]:
    """
    Score using a trained ML model.  Returns None if no model is loaded.
    """
    if _model is None:
        _load_ml_model()

    if _model is None:
        return None

    # Build feature vector in the correct order
    import numpy as np
    x = np.array([[features.get(name, 0.0) for name in FEATURE_NAMES]], dtype=np.float32)

    # XGBoost 3.x requires DMatrix; lightgbm/sklearn accept numpy directly
    if _model_type == "xgboost":
        import xgboost as xgb  # type: ignore
        dmatrix = xgb.DMatrix(x, feature_names=FEATURE_NAMES)
        raw = float(_model.predict(dmatrix)[0])
    else:
        raw = float(_model.predict(x)[0])

    # Convert raw margins/logits to probabilities, if necessary.
    if raw < 0 or raw > 1:
        import math
        raw = 1.0 / (1.0 + math.exp(-max(-709.0, min(709.0, raw))))

    return max(0.0, min(1.0, raw))


def score(features: dict[str, float]) -> float:
    """
    Main scoring entry point.  Uses ML model if available, else heuristic.

    Returns float in [0, 1].
    """
    ml_score = score_ml(features)
    if ml_score is not None:
        return ml_score
    return score_heuristic(features)
