"""
app/ml/evaluation/evaluator.py

Phase 9 — Model Evaluation.

Loads the trained model and generates a comprehensive evaluation report
including accuracy, precision, recall, F1, and confusion matrix.
Can be run standalone: python -m app.ml.evaluation.evaluator
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

REPORT_PATH  = pathlib.Path(__file__).parent / "training_report.json"
SUMMARY_PATH = pathlib.Path(__file__).parent / "evaluation_summary.json"


def load_report() -> dict:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Training report not found at {REPORT_PATH}. "
            "Run: python -m app.ml.training.train_decision_tree"
        )
    with open(REPORT_PATH) as f:
        return json.load(f)


def print_report(report: dict) -> None:
    print("\n" + "=" * 65)
    print("  APEX ML — Decision Tree Evaluation Report")
    print("=" * 65)
    print(f"\n  Model Version : {report.get('model_version', 'unknown')}")
    print(f"  Training Samples: {report.get('n_train', 0)}")
    print(f"  Test Samples    : {report.get('n_test', 0)}")
    print(f"\n{'─' * 65}")
    print(f"  {'Metric':<20} {'Score':>10}  {'Interpretation'}")
    print(f"{'─' * 65}")

    metrics = [
        ("Accuracy",   report.get("accuracy", 0),   _interp_accuracy),
        ("Precision",  report.get("precision", 0),  _interp_generic),
        ("Recall",     report.get("recall", 0),     _interp_generic),
        ("F1 Score",   report.get("f1_score", 0),   _interp_f1),
        ("CV F1 Mean", report.get("cv_f1_mean", 0), _interp_f1),
    ]

    for name, val, interp in metrics:
        bar = _bar(val)
        print(f"  {name:<20} {val:>8.4f}  {bar}  {interp(val)}")

    print(f"\n{'─' * 65}")
    print("  Feature Importances (top 10):")
    importances = report.get("feature_importances", {})
    top10 = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]
    for feat, imp in top10:
        bar = _bar(imp * 5)  # Scale for visibility
        print(f"    {feat:<35} {imp:.4f}  {bar}")

    print(f"\n{'─' * 65}")
    print("  Per-Class F1 Scores:")
    clf_report = report.get("classification_report", {})
    for cls in report.get("classes", []):
        cls_metrics = clf_report.get(cls, {})
        f1 = cls_metrics.get("f1-score", 0)
        n  = cls_metrics.get("support", 0)
        bar = _bar(f1)
        print(f"    {cls:<15} F1={f1:.3f}  n={n:<5}  {bar}")

    print(f"\n{'─' * 65}")
    print("  Confusion Matrix:")
    cm = report.get("confusion_matrix", [])
    classes = report.get("classes", [])
    if cm and classes:
        header = "         " + "  ".join(f"{c[:5]:>5}" for c in classes)
        print(f"    {header}")
        for i, row in enumerate(cm):
            row_str = "  ".join(f"{v:>5}" for v in row)
            print(f"    {classes[i]:<8} {row_str}")
    print("=" * 65 + "\n")


def generate_summary(report: dict) -> dict:
    summary = {
        "model_version":    report.get("model_version"),
        "overall_accuracy": report.get("accuracy"),
        "weighted_f1":      report.get("f1_score"),
        "cv_f1_mean":       report.get("cv_f1_mean"),
        "cv_f1_std":        report.get("cv_f1_std"),
        "assessment":       _overall_assessment(report.get("f1_score", 0)),
        "per_class": {
            cls: {
                "precision": report["classification_report"].get(cls, {}).get("precision", 0),
                "recall":    report["classification_report"].get(cls, {}).get("recall", 0),
                "f1":        report["classification_report"].get(cls, {}).get("f1-score", 0),
                "support":   report["classification_report"].get(cls, {}).get("support", 0),
            }
            for cls in report.get("classes", [])
        },
        "top_features": dict(
            sorted(
                report.get("feature_importances", {}).items(),
                key=lambda x: x[1], reverse=True
            )[:10]
        ),
    }
    return summary


def _bar(val: float, width: int = 12) -> str:
    filled = int(round(val * width))
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _interp_accuracy(v: float) -> str:
    if v >= 0.85: return "Excellent"
    if v >= 0.75: return "Good"
    if v >= 0.65: return "Acceptable"
    return "Needs improvement"


def _interp_f1(v: float) -> str:
    if v >= 0.80: return "Excellent"
    if v >= 0.70: return "Good"
    if v >= 0.60: return "Acceptable"
    return "Needs improvement"


def _interp_generic(v: float) -> str:
    if v >= 0.80: return "Strong"
    if v >= 0.70: return "Moderate"
    return "Fair"


def _overall_assessment(f1: float) -> str:
    if f1 >= 0.80:
        return "Production-ready. Model demonstrates strong generalisation across all muscle group classes."
    if f1 >= 0.70:
        return "Good performance. Suitable for production with monitoring. Consider augmenting dataset for underrepresented classes."
    if f1 >= 0.60:
        return "Acceptable for MVP. Recommend increasing dataset size and exploring ensemble methods."
    return "Below target. Increase dataset diversity, tune hyperparameters, and review feature engineering."


def run_evaluation() -> dict:
    report = load_report()
    print_report(report)
    summary = generate_summary(report)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Evaluation summary saved → {SUMMARY_PATH}")
    return summary


if __name__ == "__main__":
    run_evaluation()
