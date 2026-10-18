"""
train_real.py — Training pipeline for the personalized scheme ranking model using REAL user interaction data.

Generates training data from the ml_training_data materialized view,
trains an XGBoost model, and saves it for use by the scorer.

Usage:
    python -m services.api.ml.train_real [--output model.json] [--refresh]

The script loads user interaction data from ml_training_data view,
computes features using the same extract_features function,
and trains an XGBoost classifier.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from services.api.ml.features import extract_features, FEATURE_NAMES


def load_training_data(limit: Optional[int] = None) -> tuple[np.ndarray, np.ndarray]:
    """
    Load training data from the ml_training_data materialized view.

    Returns (X, y) where X is shape (n_samples, n_features) and y is (n_samples,).
    """
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()

    url = os.getenv('DATABASE_URL')
    if '@postgres:5432/' in url:
        import socket
        try:
            socket.gethostbyname('postgres')
        except socket.gaierror:
            url = url.replace('@postgres:5432/', '@localhost:5433/')

    conn = psycopg2.connect(url)
    cur = conn.cursor()

    query = """
        SELECT 
            age, income, gender, caste, state, education_level,
            scheme_state_code, scheme_source, confidence_score,
            min_age, max_age, max_income, rule_gender, rule_caste, rule_states, rule_education_level,
            label
        FROM ml_training_data
        WHERE age IS NOT NULL AND income IS NOT NULL
    """
    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        print("No training data found in ml_training_data view")
        return np.array([]), np.array([])

    print(f"Loaded {len(rows)} training samples")

    X_rows = []
    y_labels = []

    for row in rows:
        (age, income, gender, caste, state, education_level,
         scheme_state_code, scheme_source, confidence_score,
         min_age, max_age, max_income, rule_gender, rule_caste, rule_states, rule_education_level,
         label) = row

        # Build profile dict
        profile = {
            "age": age,
            "income": float(income) if income else None,
            "gender": gender,
            "caste": caste,
            "state": state,
            "education_level": education_level,
        }

        # Build rules dict
        rules = {
            "min_age": min_age,
            "max_age": max_age,
            "max_income": float(max_income) if max_income else None,
            "gender": rule_gender,
            "caste": rule_caste,
            "states": rule_states,
            "education_level": rule_education_level,
        }

        # Build scheme dict
        scheme = {
            "state_code": scheme_state_code,
            "source": scheme_source,
            "confidence_score": float(confidence_score) if confidence_score else 0.5,
        }

        # Extract features
        features = extract_features(profile, rules, scheme)

        X_rows.append([features.get(name, 0.0) for name in FEATURE_NAMES])
        y_labels.append(label)

    X = np.array(X_rows, dtype=np.float32)
    y = np.array(y_labels, dtype=np.int32)

    print(f"Positive samples: {(y == 1).sum()}, Negative samples: {(y == 0).sum()}")
    print(f"Feature shape: {X.shape}")

    return X, y


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

    # Handle class imbalance
    pos_weight = (y == 0).sum() / max((y == 1).sum(), 1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_NAMES)
    dtest = xgb.DMatrix(X_test, label=y_test, feature_names=FEATURE_NAMES)

    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 6,
        "eta": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 5,
        "scale_pos_weight": pos_weight,
        "seed": 42,
        "verbosity": 1,
    }

    evals_result = {}
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=200,
        evals=[(dtrain, "train"), (dtest, "test")],
        early_stopping_rounds=20,
        verbose_eval=20,
        evals_result=evals_result,
    )

    # Evaluate
    y_pred_prob = model.predict(dtest)
    y_pred = (y_pred_prob > 0.5).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "auc": float(roc_auc_score(y_test, y_pred_prob)),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "pos_weight": float(pos_weight),
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
        mapped = {}
        for k, v in imp.items():
            try:
                idx = int(k.replace('f', ''))
                name = FEATURE_NAMES[idx] if idx < len(FEATURE_NAMES) else k
            except (ValueError, IndexError):
                name = k
            mapped[name] = float(v)
        sorted_imp = sorted(mapped.items(), key=lambda x: x[1], reverse=True)
        for name, val in sorted_imp[:10]:
            print(f"  {name}: {val:.1f}")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train the scheme ranking model on REAL user data")
    parser.add_argument("--output", default="models/ranker.json", help="Output model path")
    parser.add_argument("--limit", type=int, default=None, help="Limit training samples (for testing)")
    parser.add_argument("--refresh", action="store_true", help="Refresh materialized view before training")
    args = parser.parse_args()

    if args.refresh:
        print("Refreshing ml_training_data materialized view...")
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv('DATABASE_URL')
        if '@postgres:5432/' in url:
            import socket
            try:
                socket.gethostbyname('postgres')
            except socket.gaierror:
                url = url.replace('@postgres:5432/', '@localhost:5433/')
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY ml_training_data")
        cur.close()
        conn.close()
        print("View refreshed")

    print("Loading training data from ml_training_data view...")
    X, y = load_training_data(limit=args.limit)

    if len(X) == 0:
        print("ERROR: No training data available. Need user interactions in user_events table.")
        print("Run the API with event tracking, let users interact, then refresh the view:")
        print("  REFRESH MATERIALIZED VIEW CONCURRENTLY ml_training_data;")
        sys.exit(1)

    print(f"Training on {len(X)} samples...")
    metrics = train_xgboost(X, y, output_path=args.output)

    # Save metrics
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