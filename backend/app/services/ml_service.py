"""Model loading and inference service."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import json

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.data_utils import align_features


@dataclass
class ModelBundle:
    model: Any
    feature_columns: List[str]
    labels: List[str]
    metadata: Dict[str, Any]


class MLService:
    def __init__(self, artifact_dir: str | Path | None = None):
        self.artifact_dir = Path(artifact_dir) if artifact_dir else settings.resolve_path(settings.model_artifact_dir)
        self.bundle: ModelBundle | None = None
        self.load_error: str | None = None

    @property
    def ready(self) -> bool:
        return self.bundle is not None

    def load(self) -> bool:
        try:
            model_path = self.artifact_dir / "model.joblib"
            features_path = self.artifact_dir / "feature_columns.json"
            labels_path = self.artifact_dir / "labels.json"
            meta_path = self.artifact_dir / "metadata.json"
            if not model_path.exists() or not features_path.exists():
                self.load_error = f"Model artifacts not found in {self.artifact_dir}"
                self.bundle = None
                return False
            model = joblib.load(model_path)
            feature_columns = json.loads(features_path.read_text(encoding="utf-8"))
            labels = json.loads(labels_path.read_text(encoding="utf-8")) if labels_path.exists() else list(getattr(model, "classes_", []))
            metadata = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            self.bundle = ModelBundle(model=model, feature_columns=feature_columns, labels=labels, metadata=metadata)
            self.load_error = None
            return True
        except Exception as e:
            self.bundle = None
            self.load_error = str(e)
            return False

    def ensure_loaded(self) -> None:
        if not self.ready:
            self.load()
        if not self.ready:
            raise RuntimeError(self.load_error or "ML model is not available")

    def _vector_from_features(self, mapped_features: List[str]) -> pd.DataFrame:
        assert self.bundle is not None
        row = {col: 0 for col in self.bundle.feature_columns}
        for f in mapped_features:
            if f in row:
                row[f] = 1
        df = pd.DataFrame([row], columns=self.bundle.feature_columns)
        return align_features(df, self.bundle.feature_columns)

    def predict(self, mapped_features: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        self.ensure_loaded()
        assert self.bundle is not None
        X = self._vector_from_features(mapped_features)
        model = self.bundle.model
        classes = list(getattr(model, "classes_", self.bundle.labels))
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)[0]
        else:
            # fallback: one-hot for predicted class
            pred = model.predict(X)[0]
            probs = np.array([1.0 if c == pred else 0.0 for c in classes], dtype=float)
        pairs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
        top = pairs[:top_k]
        results = []
        for cond, prob in top:
            p = float(prob)
            if p >= 0.6:
                conf = "higher model confidence"
            elif p >= 0.3:
                conf = "moderate model confidence"
            else:
                conf = "lower model confidence"
            results.append({
                "condition": str(cond),
                "probability": round(p, 6),
                "confidence_label": conf,
            })
        return results

    def feature_importance_for_conditions(self, conditions: List[str], mapped_features: List[str], top_n: int = 5) -> Dict[str, List[str]]:
        """Best-effort supporting symptoms from model coefficients/importances."""
        self.ensure_loaded()
        assert self.bundle is not None
        model = self.bundle.model
        out: Dict[str, List[str]] = {c: [] for c in conditions}
        classes = list(getattr(model, "classes_", []))
        feature_names = self.bundle.feature_columns
        active = set(mapped_features)
        try:
            if hasattr(model, "coef_") and classes:
                coef = np.array(model.coef_)
                for cond in conditions:
                    if cond not in classes:
                        continue
                    idx = classes.index(cond)
                    weights = coef[idx]
                    ranked = sorted(zip(feature_names, weights), key=lambda x: x[1], reverse=True)
                    # prefer active mapped symptoms, then high positive contributors
                    act = [f for f, _ in ranked if f in active]
                    pos = [f for f, w in ranked if w > 0 and f not in act]
                    chosen = (act + pos)[:top_n]
                    out[cond] = chosen
            elif hasattr(model, "feature_importances_"):
                imps = list(model.feature_importances_)
                ranked = sorted(zip(feature_names, imps), key=lambda x: x[1], reverse=True)
                common = [f for f, _ in ranked if f in active][:top_n]
                for cond in conditions:
                    out[cond] = common
            else:
                for cond in conditions:
                    out[cond] = [f for f in mapped_features[:top_n]]
        except Exception:
            for cond in conditions:
                out[cond] = [f for f in mapped_features[:top_n]]
        return out


ml_service = MLService()
