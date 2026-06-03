"""
app/ml/utils/helpers.py

Shared utility functions used across the ML pipeline.
"""
from __future__ import annotations
import math
from typing import Any


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    """Compute a ratio, returning None if either value is missing or denominator is 0."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def pct_of_target(current: float, target: float) -> float:
    """Return current as a percentage of target, clamped to 0–200."""
    if target == 0:
        return 0.0
    return round(min(max((current / target) * 100, 0.0), 200.0), 2)


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value between lo and hi."""
    return max(lo, min(hi, value))


def bmi(weight_kg: float, height_cm: float) -> float:
    """Body Mass Index."""
    h_m = height_cm / 100
    return round(weight_kg / (h_m ** 2), 2)


def ffmi(weight_kg: float, height_cm: float, body_fat_pct: float) -> float:
    """
    Fat-Free Mass Index — a lean mass indicator.
    FFMI = (lean_mass_kg / height_m^2) + 6.1 * (1.8 - height_m)
    Natural athletes typically top out around 25.
    """
    lean_mass = weight_kg * (1 - body_fat_pct / 100)
    h_m = height_cm / 100
    raw_ffmi = lean_mass / (h_m ** 2)
    normalised = raw_ffmi + 6.1 * (1.8 - h_m)
    return round(normalised, 2)


def score_to_grade(score: float) -> str:
    """Convert a 0–100 score to a letter grade."""
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def score_to_label(score: float) -> str:
    """Convert a 0–100 physique score to a descriptive label."""
    if score >= 90: return "Elite"
    if score >= 78: return "Advanced"
    if score >= 65: return "Developing"
    if score >= 50: return "Foundation"
    return "Beginner"


def flatten_dict(d: dict[str, Any], prefix: str = "", sep: str = ".") -> dict[str, Any]:
    """Flatten a nested dict for logging/debugging."""
    items: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}{sep}{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, key, sep))
        else:
            items[key] = v
    return items
