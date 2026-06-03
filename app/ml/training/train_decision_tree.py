"""
app/ml/training/train_decision_tree.py

Phase 3 — Decision Tree Classifier Training.

Trains a scikit-learn DecisionTreeClassifier to predict which muscle group
a user should focus on based on their body measurements and derived ratios.

Output:
  app/ml/models/decision_tree.pkl
  app/ml/models/label_encoder.pkl
  app/ml/models/feature_scaler.pkl
  app/ml/evaluation/training_report.json
"""
from __future__ import annotations

import json
import pathlib
import warnings
import numpy as np
import pandas as pd
import joblib

from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT            = pathlib.Path(__file__).parent.parent
DATASET_PATH    = ROOT / "datasets" / "physique_dataset.csv"
MODEL_DIR       = ROOT / "models"
EVALUATION_DIR  = ROOT / "evaluation"
MODEL_PATH      = MODEL_DIR  / "decision_tree.pkl"
ENCODER_PATH    = MODEL_DIR  / "label_encoder.pkl"
SCALER_PATH     = MODEL_DIR  / "feature_scaler.pkl"
REPORT_PATH     = EVALUATION_DIR / "training_report.json"

MODEL_VERSION   = "1.0.0"

# Feature columns used for training
FEATURE_COLS = [
    "height_cm", "weight_kg", "body_fat_pct",
    "chest_cm", "waist_cm", "shoulders_cm",
    "arms_cm", "forearms_cm", "neck_cm",
    "thighs_cm", "calves_cm",
    "ratio_shoulder_to_waist", "ratio_chest_to_waist",
    "ratio_hip_to_waist", "ratio_thigh_to_waist",
    "ratio_calf_to_thigh", "ratio_arm_to_neck", "ratio_forearm_to_arm",
]

TARGET_COL = "target_focus"


def load_data() -> tuple[pd.DataFrame, pd.Series]:
    if not DATASET_PATH.exists():
        print("Dataset not found — generating…")
        from app.ml.datasets.generate_dataset import generate, save_dataset
        df_full = generate(2000, 42)
        save_dataset(df_full)
    else:
        df_full = pd.read_csv(DATASET_PATH)

    # Select only feature columns that exist in the file
    available = [c for c in FEATURE_COLS if c in df_full.columns]
    X = df_full[available]
    y = df_full[TARGET_COL]
    return X, y


def train() -> dict:
    print("=" * 60)
    print("APEX — Decision Tree Training Pipeline")
    print("=" * 60)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    X, y = load_data()
    print(f"\nDataset: {len(X)} samples, {X.shape[1]} features")
    print(f"Classes: {sorted(y.unique())}")

    # 2. Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"\nLabel mapping: {dict(zip(le.classes_, le.transform(le.classes_)))}")

    # 3. Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
    print(f"\nTrain: {len(X_train)}  |  Test: {len(X_test)}")

    # 4. Build pipeline: impute → scale → decision tree
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("tree",    DecisionTreeClassifier(
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            criterion="gini",
        )),
    ])

    # 5. Cross-validation
    print("\nRunning 5-fold cross-validation…")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_weighted")
    print(f"CV F1 scores: {cv_scores.round(3)}")
    print(f"Mean CV F1:   {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # 6. Final training
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # 7. Metrics
    acc    = accuracy_score(y_test, y_pred)
    prec   = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec    = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1     = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    report = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)
    cm     = confusion_matrix(y_test, y_pred).tolist()

    print(f"\n{'─'*40}")
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1 Score  : {f1:.4f}")
    print(f"{'─'*40}")

    # 8. Feature importance (from the tree step)
    tree_step = pipeline.named_steps["tree"]
    feature_names = X.columns.tolist()
    importances = dict(zip(feature_names, tree_step.feature_importances_.round(4)))
    top5 = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\nTop 5 features:")
    for feat, imp in top5:
        print(f"  {feat:<35} {imp:.4f}")

    # 9. Save artefacts
    joblib.dump(pipeline, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"\nModel saved   → {MODEL_PATH}")
    print(f"Encoder saved → {ENCODER_PATH}")

    # 10. Save evaluation report
    eval_report = {
        "model_version":  MODEL_VERSION,
        "n_train":        int(len(X_train)),
        "n_test":         int(len(X_test)),
        "accuracy":       round(acc, 4),
        "precision":      round(prec, 4),
        "recall":         round(rec, 4),
        "f1_score":       round(f1, 4),
        "cv_f1_mean":     round(float(cv_scores.mean()), 4),
        "cv_f1_std":      round(float(cv_scores.std()), 4),
        "confusion_matrix": cm,
        "classification_report": report,
        "feature_importances": importances,
        "classes": le.classes_.tolist(),
    }

    with open(REPORT_PATH, "w") as f:
        json.dump(eval_report, f, indent=2)
    print(f"Report saved  → {REPORT_PATH}")

    return eval_report


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent.parent))
    train()
