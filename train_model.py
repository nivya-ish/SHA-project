"""Reusable model training script for Smart Health Assistant.

Usage:
  py train_model.py --train data/raw/Training.csv --test data/raw/Testing.csv --artifacts ml/artifacts
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

# Ensure backend package importable when run from project root
ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score

from app.ml.data_utils import load_dataset_csv, save_json


def evaluate_model(model, X, y, labels):
    preds = model.predict(X)
    acc = float(accuracy_score(y, preds))
    precision, recall, f1, _ = precision_recall_fscore_support(y, preds, average="weighted", zero_division=0)
    report = classification_report(y, preds, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y, preds, labels=labels)
    return {
        "accuracy": acc,
        "precision_weighted": float(precision),
        "recall_weighted": float(recall),
        "f1_weighted": float(f1),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "labels_order": labels,
        "predictions_sample_count": int(len(preds)),
    }, preds


def select_and_train(X_train, y_train):
    candidates = []
    # Candidate 1: Logistic Regression (good for binary sparse features)
    lr = LogisticRegression(max_iter=2000, solver="lbfgs")
    candidates.append(("LogisticRegression", lr, {"max_iter": 2000, "solver": "lbfgs"}))
    # Candidate 2: Random Forest
    rf = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1, class_weight=None)
    candidates.append(("RandomForestClassifier", rf, {"n_estimators": 300, "random_state": 42, "class_weight": None}))

    # Small CV on training data for selection (stratified)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    best = None
    for name, model, params in candidates:
        try:
            scores = cross_val_score(model, X_train, y_train, cv=skf, scoring="f1_weighted", n_jobs=-1)
            cv_mean = float(np.mean(scores))
            cv_std = float(np.std(scores))
        except Exception:
            # fallback without parallel
            try:
                scores = cross_val_score(model, X_train, y_train, cv=skf, scoring="f1_weighted")
                cv_mean = float(np.mean(scores))
                cv_std = float(np.std(scores))
            except Exception as e:
                cv_mean = -1.0
                cv_std = 0.0
        record = {"name": name, "model": model, "params": params, "cv_f1_weighted_mean": cv_mean, "cv_f1_weighted_std": cv_std}
        if best is None or record["cv_f1_weighted_mean"] > best["cv_f1_weighted_mean"]:
            best = record

    assert best is not None
    best["model"].fit(X_train, y_train)
    return best, candidates


def main():
    parser = argparse.ArgumentParser(description="Train Smart Health Assistant ML model")
    parser.add_argument("--train", default="data/raw/Training.csv", help="Path to training CSV")
    parser.add_argument("--test", default="data/raw/Testing.csv", help="Path to test CSV")
    parser.add_argument("--artifacts", default="ml/artifacts", help="Directory to save artifacts")
    parser.add_argument("--label-column", default=None, help="Label/target column name (auto-detected if omitted)")
    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    train_bundle = load_dataset_csv(args.train, label_column=args.label_column)
    test_bundle = load_dataset_csv(args.test, label_column=train_bundle.label_column)

    # Align test features to training feature order
    X_train = train_bundle.X
    y_train = train_bundle.y
    X_test = test_bundle.X.reindex(columns=train_bundle.feature_columns, fill_value=0)
    y_test = test_bundle.y

    # Ensure label sets info
    labels = sorted(list(pd.Index(y_train.unique()).union(pd.Index(y_test.unique()))))

    best, candidates = select_and_train(X_train, y_train)
    model = best["model"]

    train_metrics, _ = evaluate_model(model, X_train, y_train, labels)
    test_metrics, _ = evaluate_model(model, X_test, y_test, labels)

    # Save artifacts
    joblib.dump(model, artifacts_dir / "model.joblib")
    save_json(artifacts_dir / "feature_columns.json", train_bundle.feature_columns)
    save_json(artifacts_dir / "labels.json", labels)

    candidate_summary = []
    for name, _, params, *_ in []:
        pass
    # rebuild candidate summary with cv results
    # (recompute lightweight summary from best/candidates structure)
    for c in candidates:
        # values captured in loop? not stored except best; recompute quickly for metadata clarity
        candidate_summary.append({"name": c[0], "params": c[2]})

    from datetime import timezone
    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "selected_algorithm": best["name"],
        "selected_params": best["params"],
        "selection_metric": "f1_weighted_cv_mean",
        "selection_cv_f1_weighted_mean": best["cv_f1_weighted_mean"],
        "selection_cv_f1_weighted_std": best["cv_f1_weighted_std"],
        "candidate_algorithms": [
            {"name": "LogisticRegression", "params": {"max_iter": 2000, "solver": "lbfgs"}},
            {"name": "RandomForestClassifier", "params": {"n_estimators": 300, "random_state": 42, "class_weight": None}},
        ],
        "label_column": train_bundle.label_column,
        "num_features": len(train_bundle.feature_columns),
        "num_classes": len(labels),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "train_dataset_notes": train_bundle.notes,
        "test_dataset_notes": test_bundle.notes,
        "train_metrics": {k: v for k, v in train_metrics.items() if k not in {"classification_report", "confusion_matrix", "labels_order"}},
        "test_metrics": {k: v for k, v in test_metrics.items() if k not in {"classification_report", "confusion_matrix", "labels_order"}},
    }
    save_json(artifacts_dir / "metadata.json", metadata)
    save_json(artifacts_dir / "train_classification_report.json", train_metrics["classification_report"])
    save_json(artifacts_dir / "test_classification_report.json", test_metrics["classification_report"])
    save_json(artifacts_dir / "test_confusion_matrix.json", {
        "labels": test_metrics["labels_order"],
        "matrix": test_metrics["confusion_matrix"],
    })
    save_json(artifacts_dir / "train_confusion_matrix.json", {
        "labels": train_metrics["labels_order"],
        "matrix": train_metrics["confusion_matrix"],
    })

    print("Training complete.")
    print(f"Selected algorithm: {best['name']}")
    print(f"Artifacts saved to: {artifacts_dir}")
    print(f"Train accuracy: {train_metrics['accuracy']:.4f} | Test accuracy: {test_metrics['accuracy']:.4f}")
    print(f"Test weighted F1: {test_metrics['f1_weighted']:.4f}")
    print(json.dumps({
        "selected_algorithm": best["name"],
        "test_metrics_summary": metadata["test_metrics"],
        "train_metrics_summary": metadata["train_metrics"],
        "num_features": metadata["num_features"],
        "num_classes": metadata["num_classes"],
    }, indent=2))


if __name__ == "__main__":
    main()
