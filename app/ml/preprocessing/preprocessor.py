"""
app/ml/preprocessing/preprocessor.py

Transforms raw PhysiqueInput into normalised feature vectors
ready for the ratio engine and the scikit-learn model.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from app.ml.utils.schemas import PhysiqueInput
from app.ml.utils.helpers import safe_ratio, bmi, ffmi


FEATURE_NAMES = [
    "height_cm", "weight_kg", "body_fat_pct",
    "chest_cm", "waist_cm", "shoulders_cm",
    "arms_cm", "forearms_cm", "neck_cm",
    "thighs_cm", "calves_cm",
    # Derived ratios
    "shoulder_to_waist", "chest_to_waist", "hip_to_waist",
    "thigh_to_waist", "calf_to_thigh", "arm_to_neck", "forearm_to_arm",
    # Composite
    "bmi", "ffmi",
]


@dataclass
class ProcessedFeatures:
    """Holds both the raw filled values and the derived ratio features."""
    raw: dict[str, float | None]
    ratios: dict[str, float | None]
    composites: dict[str, float | None]
    feature_vector: np.ndarray          # Used by scikit-learn model
    feature_names: list[str]
    missing_fields: list[str] = field(default_factory=list)
    completeness_pct: float = 0.0


class Preprocessor:
    """
    Converts a PhysiqueInput schema into a ProcessedFeatures object.

    Steps:
      1. Extract raw measurements (handle None gracefully)
      2. Compute derived ratios
      3. Compute composite indices (BMI, FFMI)
      4. Build a flat numeric feature vector (NaN for missing values)
      5. Report completeness
    """

    def process(self, data: PhysiqueInput) -> ProcessedFeatures:
        raw = self._extract_raw(data)
        ratios = self._compute_ratios(raw)
        composites = self._compute_composites(raw)
        vector, names = self._build_vector(raw, ratios, composites)
        missing = [k for k, v in raw.items() if v is None]
        filled = sum(1 for v in raw.values() if v is not None)
        completeness = round((filled / len(raw)) * 100, 1)

        return ProcessedFeatures(
            raw=raw,
            ratios=ratios,
            composites=composites,
            feature_vector=vector,
            feature_names=names,
            missing_fields=missing,
            completeness_pct=completeness,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _extract_raw(self, data: PhysiqueInput) -> dict[str, float | None]:
        return {
            "height_cm":    data.height_cm,
            "weight_kg":    data.weight_kg,
            "body_fat_pct": data.body_fat_pct,
            "chest_cm":     data.chest_cm,
            "waist_cm":     data.waist_cm,
            "shoulders_cm": data.shoulders_cm,
            "arms_cm":      data.arms_cm,
            "forearms_cm":  data.forearms_cm,
            "neck_cm":      data.neck_cm,
            "thighs_cm":    data.thighs_cm,
            "calves_cm":    data.calves_cm,
            "hips_cm":      data.hips_cm,
        }

    def _compute_ratios(self, raw: dict) -> dict[str, float | None]:
        w = raw.get("waist_cm")
        return {
            "shoulder_to_waist": safe_ratio(raw.get("shoulders_cm"), w),
            "chest_to_waist":    safe_ratio(raw.get("chest_cm"), w),
            "hip_to_waist":      safe_ratio(raw.get("hips_cm"), w),
            "thigh_to_waist":    safe_ratio(raw.get("thighs_cm"), w),
            "calf_to_thigh":     safe_ratio(raw.get("calves_cm"), raw.get("thighs_cm")),
            "arm_to_neck":       safe_ratio(raw.get("arms_cm"), raw.get("neck_cm")),
            "forearm_to_arm":    safe_ratio(raw.get("forearms_cm"), raw.get("arms_cm")),
        }

    def _compute_composites(self, raw: dict) -> dict[str, float | None]:
        h, w, bf = raw.get("height_cm"), raw.get("weight_kg"), raw.get("body_fat_pct")
        return {
            "bmi":  bmi(w, h)  if h and w else None,
            "ffmi": ffmi(w, h, bf) if h and w and bf else None,
        }

    def _build_vector(
        self,
        raw: dict,
        ratios: dict,
        composites: dict,
    ) -> tuple[np.ndarray, list[str]]:
        core_keys = [
            "height_cm", "weight_kg", "body_fat_pct",
            "chest_cm", "waist_cm", "shoulders_cm",
            "arms_cm", "forearms_cm", "neck_cm",
            "thighs_cm", "calves_cm",
        ]
        ratio_keys = list(ratios.keys())
        composite_keys = list(composites.keys())

        names = core_keys + ratio_keys + composite_keys
        values: list[float] = []

        for k in core_keys:
            v = raw.get(k)
            values.append(float(v) if v is not None else np.nan)
        for k in ratio_keys:
            v = ratios.get(k)
            values.append(float(v) if v is not None else np.nan)
        for k in composite_keys:
            v = composites.get(k)
            values.append(float(v) if v is not None else np.nan)

        return np.array(values, dtype=np.float32), names
