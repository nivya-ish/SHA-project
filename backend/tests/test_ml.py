import json
from pathlib import Path

import joblib

from app.ml.data_utils import load_dataset_csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = PROJECT_ROOT / "ml" / "artifacts"
TRAIN_CSV = PROJECT_ROOT / "data" / "raw" / "Training.csv"


def test_model_artifacts_exist_and_load():
    assert (ARTIFACTS / "model.joblib").exists()
    assert (ARTIFACTS / "feature_columns.json").exists()
    assert (ARTIFACTS / "metadata.json").exists()
    model = joblib.load(ARTIFACTS / "model.joblib")
    feature_columns = json.loads((ARTIFACTS / "feature_columns.json").read_text(encoding="utf-8"))
    assert hasattr(model, "predict")
    assert len(feature_columns) > 0


def test_feature_consistency_training_and_inference():
    bundle = load_dataset_csv(TRAIN_CSV)
    feature_columns = json.loads((ARTIFACTS / "feature_columns.json").read_text(encoding="utf-8"))
    assert feature_columns == bundle.feature_columns
    model = joblib.load(ARTIFACTS / "model.joblib")
    sample = bundle.X.iloc[:5]
    preds = model.predict(sample[feature_columns])
    assert len(preds) == 5


def test_prediction_with_synthetic_feature_vector():
    from app.services.ml_service import MLService
    svc = MLService(artifact_dir=ARTIFACTS)
    assert svc.load() is True
    # pick a known symptom combination from training row
    bundle = load_dataset_csv(TRAIN_CSV)
    row0 = bundle.X.iloc[0]
    active = [c for c in bundle.feature_columns if int(row0[c]) == 1]
    preds = svc.predict(active, top_k=3)
    assert len(preds) >= 1
    assert "condition" in preds[0] and "probability" in preds[0]
    assert 0.0 <= preds[0]["probability"] <= 1.0
