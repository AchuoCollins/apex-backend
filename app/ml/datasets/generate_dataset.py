"""
app/ml/datasets/generate_dataset.py

Phase 4 — Synthetic Dataset Generation.

Creates 2000 realistic physique records with labelled training focus targets.
The dataset is used to train the Decision Tree classifier.

Generation strategy:
  1. Sample realistic body measurements using gender-stratified normal distributions
  2. Compute all ratios
  3. Compare ratios to targets → identify the most lagging muscle group
  4. Label = the muscle group most in need of training focus
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pathlib
from typing import Literal

SEED = 42
N_SAMPLES = 2000
DATASET_PATH = pathlib.Path(__file__).parent / "physique_dataset.csv"

# ── Anthropometric distributions (mean, std) by gender ───────────────────────
# Based on epidemiological data (NHANES, sports science literature)

MALE_PARAMS = {
    "height_cm":    (178.0, 7.0),
    "weight_kg":    (82.0,  14.0),
    "body_fat_pct": (18.0,  6.0),
    "chest_cm":     (100.0, 8.0),
    "waist_cm":     (84.0,  9.0),
    "shoulders_cm": (118.0, 8.0),
    "arms_cm":      (34.0,  4.0),
    "forearms_cm":  (28.0,  3.0),
    "neck_cm":      (38.0,  3.0),
    "thighs_cm":    (58.0,  6.0),
    "calves_cm":    (36.0,  4.0),
    "hips_cm":      (96.0,  7.0),
}

FEMALE_PARAMS = {
    "height_cm":    (165.0, 6.0),
    "weight_kg":    (65.0,  11.0),
    "body_fat_pct": (26.0,  6.0),
    "chest_cm":     (90.0,  7.0),
    "waist_cm":     (74.0,  8.0),
    "shoulders_cm": (104.0, 7.0),
    "arms_cm":      (28.0,  3.5),
    "forearms_cm":  (23.0,  2.5),
    "neck_cm":      (33.0,  2.5),
    "thighs_cm":    (56.0,  6.0),
    "calves_cm":    (35.0,  3.5),
    "hips_cm":      (100.0, 8.0),
}

# Ratio targets (mirrors constants.py)
RATIO_TARGETS = {
    "shoulder_to_waist": 1.618,
    "chest_to_waist":    1.40,
    "hip_to_waist":      1.25,
    "thigh_to_waist":    0.75,
    "calf_to_thigh":     0.60,
    "arm_to_neck":       1.00,
    "forearm_to_arm":    0.80,
}

RATIO_TO_LABEL = {
    "shoulder_to_waist": "shoulders",
    "chest_to_waist":    "chest",
    "hip_to_waist":      "glutes",
    "thigh_to_waist":    "legs",
    "calf_to_thigh":     "calves",
    "arm_to_neck":       "arms",
    "forearm_to_arm":    "forearms",
}

FOCUS_LABELS = ["shoulders", "chest", "glutes", "legs", "calves", "arms", "forearms"]


def _sample_person(rng: np.random.Generator, gender: Literal["male", "female"]) -> dict:
    params = MALE_PARAMS if gender == "male" else FEMALE_PARAMS
    person: dict = {"gender": gender}
    for field, (mean, std) in params.items():
        value = rng.normal(mean, std)
        # Apply physiological bounds
        if field == "body_fat_pct":
            value = np.clip(value, 5, 45)
        elif field in ("height_cm",):
            value = np.clip(value, 150, 215)
        else:
            value = max(value, 5.0)
        person[field] = round(float(value), 1)
    return person


def _compute_ratios(p: dict) -> dict:
    w = p["waist_cm"]
    return {
        "shoulder_to_waist": p["shoulders_cm"] / w,
        "chest_to_waist":    p["chest_cm"] / w,
        "hip_to_waist":      p["hips_cm"] / w,
        "thigh_to_waist":    p["thighs_cm"] / w,
        "calf_to_thigh":     p["calves_cm"] / p["thighs_cm"],
        "arm_to_neck":       p["arms_cm"] / p["neck_cm"],
        "forearm_to_arm":    p["forearms_cm"] / p["arms_cm"],
    }


def _label_focus(ratios: dict) -> str:
    """
    Label = the ratio furthest below its target (as a % deficit).
    This is the muscle group most in need of training focus.
    """
    worst_label = "shoulders"
    worst_deficit = -999.0

    for ratio_name, target in RATIO_TARGETS.items():
        current = ratios[ratio_name]
        deficit = (target - current) / target  # positive = below target
        if deficit > worst_deficit:
            worst_deficit = deficit
            worst_label = RATIO_TO_LABEL[ratio_name]

    return worst_label


def generate(n: int = N_SAMPLES, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    for i in range(n):
        gender: Literal["male", "female"] = "male" if rng.random() > 0.4 else "female"
        person = _sample_person(rng, gender)

        # Occasionally inject a strongly lagging group to balance labels
        if i % 7 == 0:
            # Force a calf deficit
            person["calves_cm"] = max(person["thighs_cm"] * 0.45, 20.0)
        elif i % 11 == 0:
            # Force arm deficit
            person["arms_cm"] = max(person["neck_cm"] * 0.75, 20.0)

        ratios = _compute_ratios(person)
        label  = _label_focus(ratios)

        row = {**person, **{f"ratio_{k}": round(v, 4) for k, v in ratios.items()}, "target_focus": label}
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def save_dataset(df: pd.DataFrame, path: pathlib.Path = DATASET_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Dataset saved → {path}  ({len(df)} rows)")
    print(f"Label distribution:\n{df['target_focus'].value_counts()}")


if __name__ == "__main__":
    df = generate(N_SAMPLES, SEED)
    save_dataset(df)
