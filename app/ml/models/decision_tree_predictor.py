"""
app/ml/models/decision_tree_predictor.py

Loads the trained Decision Tree pipeline and serves weak-point predictions.
Implements the BasePhysiquePredictor interface defined in the stub.
"""
from __future__ import annotations

import pathlib
import numpy as np
import joblib
import json

from app.ml.utils.schemas import (
    PhysiqueInput, DecisionTreeResult, WeakPointPrediction,
)
from app.ml.preprocessing.preprocessor import Preprocessor

MODEL_DIR    = pathlib.Path(__file__).parent
MODEL_PATH   = MODEL_DIR / "decision_tree.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"
REPORT_PATH  = MODEL_DIR.parent / "evaluation" / "training_report.json"
MODEL_VERSION = "1.0.0"


class DecisionTreePredictor:
    """
    Thin wrapper around the trained sklearn pipeline.
    Handles loading, feature preparation, and returning structured results.
    """

    def __init__(self) -> None:
        self._pipeline = None
        self._encoder  = None
        self._feature_importance: dict[str, float] = {}
        self._loaded = False

    def load(self) -> None:
        """Load model artefacts from disk. Call once at startup."""
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run: python -m app.ml.training.train_decision_tree"
            )
        self._pipeline = joblib.load(MODEL_PATH)
        self._encoder  = joblib.load(ENCODER_PATH)

        if REPORT_PATH.exists():
            with open(REPORT_PATH) as f:
                report = json.load(f)
            self._feature_importance = report.get("feature_importances", {})

        self._loaded = True

    def is_ready(self) -> bool:
        return self._loaded and self._pipeline is not None

    def predict(self, data: PhysiqueInput) -> DecisionTreeResult:
        if not self.is_ready():
            self.load()

        preprocessor = Preprocessor()
        features = preprocessor.process(data)

        # Build feature vector matching training columns
        from app.ml.training.train_decision_tree import FEATURE_COLS
        col_map = {
            **{k: v for k, v in features.raw.items()},
            **{f"ratio_{k}": v for k, v in features.ratios.items()},
        }

        vector = []
        available_names = []
        for col in FEATURE_COLS:
            val = col_map.get(col)
            vector.append(float(val) if val is not None else np.nan)
            available_names.append(col)

        X = np.array([vector])

        # Probabilities per class
        proba = self._pipeline.predict_proba(X)[0]
        classes = self._encoder.classes_

        predictions = sorted(
            [
                WeakPointPrediction(
                    muscle_group=cls,
                    confidence=round(float(prob), 4),
                    is_primary_focus=(i == int(np.argmax(proba))),
                )
                for i, (cls, prob) in enumerate(zip(classes, proba))
            ],
            key=lambda p: p.confidence,
            reverse=True,
        )

        top_focus = predictions[0].muscle_group if predictions else "unknown"

        return DecisionTreeResult(
            predictions=predictions,
            model_version=MODEL_VERSION,
            top_focus=top_focus,
            feature_importance=self._feature_importance,
        )


# Singleton instance — shared across requests
_predictor_instance: DecisionTreePredictor | None = None


def get_predictor() -> DecisionTreePredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = DecisionTreePredictor()
    return _predictor_instance
