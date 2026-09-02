"""
train.py — Training pipeline for the personalized scheme ranking model.

Generates synthetic training data from the existing scheme database,
trains an XGBoost model, and saves it for use by the scorer.

Usage:
    python -m services.api.ml.train [--synthetic] [--output model.json]

The synthetic mode creates (profile, scheme, relevance_label) triples
by simulating different user profiles against the scheme database.
This gives us a starting dataset until real user interaction data
(clicks, applications) becomes available.
"""

from __future__ import annotations

import os
import sys
import json
import random
import argparse
from pathlib import Path
from typing import Optional

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from services.api.ml.features import extract_features, FEATURE_NAMES


# ── Synthetic profile generation ────────────────────────────────────────────

SAMPLE_PROFILES = [
    # Diverse Indian user profiles
    {"age": 18, "income": 80000, "gender": "female", "caste": "SC", "state": "TN", "education_level": "12th_pass"},
    {"age": 22, "income": 300000, "gender": "male", "caste": "OBC", "state": "KA", "education_level": "graduate"},
    {"age": 30, "income": 600000, "gender": "female", "caste": "general", "state": "MH", "education_level": "post_graduate"},
    {"age": 16, "income": 50000, "gender": "male", "caste": "ST", "state": "RJ", "education_level": "10th_pass"},
    {"age": 25, "income": 150000, "gender": "female", "caste": "OBC", "state": "UP", "education_level": "graduate"},
    {"age": 40, "income": 800000, "gender": "male", "caste": "general", "state": "DL", "education_level": "post_graduate"},
    {"age": 19, "income": 100000, "gender": "female", "caste": "SC", "state": "BR", "education_level": "12th_pass"},
    {"age": 28, "income": 250000, "gender": "male", "caste": "general", "state": "GJ", "education_level": "graduate"},
    {"age": 21, "income": 120000, "gender": "female", "caste": "ST", "state": "ML", "education_level": "graduate"},
    {"age": 35, "income": 500000, "gender": "male", "caste": "OBC", "state": "AP", "education_level": "post_graduate"},
    {"age": 17, "income": 60000, "gender": "female", "caste": "general", "state": "KL", "education_level": "10th_pass"},
    {"age": 24, "income": 180000, "gender": "male", "caste": "SC", "state": "WB", "education_level": "graduate"},
    {"age": 20, "income": 90000, "gender": "female", "caste": "OBC", "state": "TG", "education_level": "12th_pass"},
    {"age": 45, "income": 1000000, "gender": "male", "caste": "general", "state": "IN", "education_level": "post_graduate"},
    {"age": 23, "income": 200000, "gender": "female", "caste": "SC", "state": "CG", "education_level": "graduate"},
    # Edge cases
    {"age": 15, "income": 40000, "gender": "male", "caste": "ST", "state": "JH", "education_level": "8th_pass"},
    {"age": 60, "income": 300000, "gender": "female", "caste": "general", "state": "HP", "education_level": "graduate"},
    {"age": 26, "income": 0, "gender": "male", "caste": "SC", "state": "OD", "education_level": "graduate"},
    {"age": 22, "income": 500000, "gender": "others", "caste": "general", "state": "GA", "education_level": "post_graduate"},
    {"age": 19, "income": 70000, "gender": "female", "caste": "OBC", "state": "AS", "education_level": "12th_pass"},
]


def _generate_synthetic_label(features: dict[str, float]) -> int:
    """
    Generate a relevance label (0 or 1) from features for synthetic training.

    This is a heuristic labeler that approximates what a real user would
    consider "relevant".  It's noisy by design — the model will learn
    to generalise despite the noise.
    """
    # Strong positive: high eligibility match + state match
    if features["eligibility_match_ratio"] >= 0.8 and features["state_eligible"] > 0.5:
        return 1

    # Moderate positive: passes most rules
    if features["eligibility_match_ratio"] >= 0.6:
        return 1

    # Strong negative: fails hard rules
    if features["state_eligible"] < 0.5 or features["caste_eligible"] < 0.5:
        return 0

    # Edge case: income mismatch
    if features["income_eligible"] < 0.5:
        return 0

    # Default: 50/50 with slight bias toward eligible
    return random.choices([0, 1], weights=[0.4, 0.6])[0]


def generate_synthetic_dataset(
    schemes_with_rules: list[dict],
    n_profiles: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a synthetic training dataset.

    Returns (X, y) where X is shape (n_samples, n_features) and y is (n_samples,).
    """
    X_rows = []
    y_labels = []

    # Expand profiles with some variation
    profiles = list(SAMPLE_PROFILES)
    while len(profiles) < n_profiles:
        base = random.choice(SAMPLE_PROFILES)
        varied = dict(base)
        # Add noise
        varied["age"] = max(10, min(70, varied["age"] + random.randint(-3, 3)))
        varied["income"] = max(0, varied["income"] + random.randint(-20000, 20000))
        if random.random() < 0.1:
            varied["state"] = random.choice(["IN", "MH", "KA", "TN", "DL", "UP"])
        profiles.append(varied)

    random.shuffle(profiles)

    for profile in profiles[:n_profiles]:
        for item in schemes_with_rules[:50]:  # Sample 50 schemes per profile
            scheme = item.get("scheme", item)
            rules = item.get("rules")

            features = extract_features(profile, rules, scheme)
            label = _generate_synthetic_label(features)

            X_rows.append([features.get(name, 0.0) for name in FEATURE_NAMES])
            y_labels.append(label)

    return np.array(X_rows, dtype=np.float32), np.array(y_labels, dtype=np.int32)


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    output_path: str = "models/ranker.json",
) -> dict:
    """
    Train an XGBoost classifier and save the model.

    Returns evaluation metrics.
    """
    try:
        import xgboost as xgb
    except ImportError:
        print("ERROR: xgboost not installed. Run: pip install xgboost")
        sys.exit(1)

    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_NAMES)
    dtest = xgb.DMatrix(X_test, label=y_test, feature_names=FEATURE_NAMES)

    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 5,
        "eta": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "seed": 42,
        "verbosity": 0,
    }

    model = xgb.train(
        params,
        dtrain,
        num_boost_round=100,
        evals=[(dtrain, "train"), (dtest, "test")],
        early_stopping_rounds=10,
        verbose_eval=False,
    )

    # Evaluate
    y_pred_prob = model.predict(dtest)
    y_pred = (y_pred_prob > 0.5).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "auc": float(roc_auc_score(y_test, y_pred_prob)),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_importance": model.get_score(importance_type='gain'),
    }

    # Save model
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    model.save_model(output_path)
    print(f"Model saved to {output_path}")
    print(f"Accuracy: {metrics['accuracy']:.3f}, AUC: {metrics['auc']:.3f}")

    # Print top features
    print("\nTop features by importance:")
    imp = metrics["feature_importance"]
    if isinstance(imp, dict) and imp:
        # Map f0 -> feature name if needed
        mapped = {}
        for k, v in imp.items():
            try:
                idx = int(k.replace('f', ''))
                name = FEATURE_NAMES[idx] if idx < len(FEATURE_NAMES) else k
            except (ValueError, IndexError):
                name = k
            mapped[name] = float(v)
        sorted_imp = sorted(mapped.items(), key=lambda x: x[1], reverse=True)
        for name, val in sorted_imp[:5]:
            print(f"  {name}: {val:.1f}")
    elif isinstance(imp, dict):
        print("  No features were used (model is trivial)")
    else:
        print(f"  (raw: {imp})")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train the scheme ranking model")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic training data")
    parser.add_argument("--output", default="models/ranker.json", help="Output model path")
    parser.add_argument("--profiles", type=int, default=200, help="Number of synthetic profiles")
    args = parser.parse_args()

    if not args.synthetic:
        print("Currently only --synthetic mode is supported.")
        print("In production, this would load user interaction data from the database.")
        print("Run with --synthetic to generate and train on synthetic data.")
        return

    print("Generating synthetic training data...")
    # For now, use empty scheme list — in production, load from DB
    synthetic_schemes = [
        {
            "scheme": {
                "id": f"scheme_{i}",
                "name": f"Scheme {i}",
                "state_code": random.choice(["IN", "MH", "KA", "TN", "DL", None]),
                "source": random.choice(["scholarships.gov.in", "india.gov.in", "example.com"]),
                "confidence_score": random.uniform(0.5, 0.95),
            },
            "rules": {
                "min_age": random.choice([None, 16, 18, 21, 25]),
                "max_age": random.choice([None, 25, 30, 35, 40]),
                "max_income": random.choice([None, 100000, 250000, 500000, 800000]),
                "gender": random.choice([None, ["male"], ["female"]]),
                "caste": random.choice([None, ["SC"], ["ST"], ["OBC"], ["SC", "ST"]]),
                "states": random.choice([None, ["MH"], ["KA"], ["TN"], ["IN"]]),
                "education_level": random.choice([None, "10th_pass", "12th_pass", "graduate"]),
            },
        }
        for i in range(50)
    ]

    X, y = generate_synthetic_dataset(synthetic_schemes, n_profiles=args.profiles)
    print(f"Generated {len(X)} samples ({(y == 1).sum()} positive, {(y == 0).sum()} negative)")

    metrics = train_xgboost(X, y, output_path=args.output)

    # Save metrics (ensure all values are JSON-serializable)
    metrics_path = args.output.replace(".json", "_metrics.json")
    serializable_metrics = {
        k: (float(v) if isinstance(v, (int, float)) else v)
        for k, v in metrics.items()
    }
    if isinstance(serializable_metrics.get("feature_importance"), dict):
        serializable_metrics["feature_importance"] = {
            k: float(v) for k, v in serializable_metrics["feature_importance"].items()
        }
    with open(metrics_path, "w") as f:
        json.dump(serializable_metrics, f, indent=2)
    print(f"Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
