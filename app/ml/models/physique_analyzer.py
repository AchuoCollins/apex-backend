"""
app/ml/models/physique_analyzer.py

Phase 1 — Physique Analysis Engine.

Computes aesthetic ratio scores, an overall physique score,
a symmetry score, and identifies strong / weak muscle groups.
All calculations are based on established sports science literature.
"""
from __future__ import annotations

from app.ml.preprocessing.preprocessor import Preprocessor, ProcessedFeatures
from app.ml.utils.constants import (
    RATIO_TARGETS, RATIO_WEIGHTS, RATIO_TO_PRIMARY_MUSCLE,
    OPTIMAL_BAND_PCT, DEVELOPING_LOW_PCT, LAGGING_THRESHOLD,
    STATUS_OPTIMAL, STATUS_DEVELOPING, STATUS_LAGGING, STATUS_OVERDEVELOPED,
    PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
)
from app.ml.utils.helpers import pct_of_target, score_to_grade, score_to_label
from app.ml.utils.schemas import (
    PhysiqueInput, PhysiqueAnalysisResult, RatioResult, MuscleSummary,
)


class PhysiqueAnalyzer:
    """
    Analyses body measurements and returns a comprehensive physique report.

    Algorithm:
      1. Preprocess raw measurements → derived ratios
      2. Score each ratio against its target (0–100 per ratio)
      3. Compute weighted overall physique score
      4. Compute symmetry score from variance of ratio scores
      5. Classify ratios: lagging / developing / optimal / overdeveloped
      6. Identify strong and weak areas
      7. Generate human-readable interpretation
    """

    def __init__(self) -> None:
        self._preprocessor = Preprocessor()

    def analyse(self, data: PhysiqueInput) -> PhysiqueAnalysisResult:
        features = self._preprocessor.process(data)
        ratios   = self._score_ratios(features)
        physique_score  = self._compute_physique_score(ratios)
        symmetry_score  = self._compute_symmetry_score(ratios)
        strong, weak    = self._classify_areas(ratios)
        lagging         = [r.primary_muscle for r in ratios if r.status == STATUS_LAGGING]

        return PhysiqueAnalysisResult(
            physique_score=physique_score,
            symmetry_score=symmetry_score,
            grade=score_to_grade(physique_score),
            label=score_to_label(physique_score),
            bmi=features.composites.get("bmi"),
            ffmi=features.composites.get("ffmi"),
            ratios=ratios,
            strong_areas=strong,
            weak_areas=weak,
            lagging_groups=lagging,
            data_completeness=features.completeness_pct,
            interpretation=self._interpret(physique_score, lagging, strong),
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _score_ratios(self, features: ProcessedFeatures) -> list[RatioResult]:
        results: list[RatioResult] = []

        for ratio_name, target in RATIO_TARGETS.items():
            current = features.ratios.get(ratio_name)
            if current is None:
                continue  # Skip ratios we can't compute

            pct   = pct_of_target(current, target)
            diff  = round(current - target, 4)
            status = self._classify_ratio(pct)
            priority = self._ratio_priority(ratio_name, status)
            muscle = RATIO_TO_PRIMARY_MUSCLE.get(ratio_name, ratio_name.replace("_", " ").title())

            results.append(RatioResult(
                name=ratio_name.replace("_", " ").title(),
                current=round(current, 3),
                target=round(target, 3),
                pct_of_target=pct,
                status=status,
                diff=diff,
                primary_muscle=muscle,
                priority=priority,
            ))

        return results

    def _classify_ratio(self, pct: float) -> str:
        if pct < LAGGING_THRESHOLD:
            return STATUS_LAGGING
        if pct < 100 - OPTIMAL_BAND_PCT:
            return STATUS_DEVELOPING
        if pct <= 100 + OPTIMAL_BAND_PCT:
            return STATUS_OPTIMAL
        return STATUS_OVERDEVELOPED

    def _ratio_priority(self, ratio_name: str, status: str) -> str:
        weight = RATIO_WEIGHTS.get(ratio_name, 0.1)
        if status == STATUS_LAGGING:
            return PRIORITY_HIGH if weight >= 0.15 else PRIORITY_MEDIUM
        if status == STATUS_DEVELOPING:
            return PRIORITY_MEDIUM if weight >= 0.15 else PRIORITY_LOW
        return PRIORITY_LOW

    def _compute_physique_score(self, ratios: list[RatioResult]) -> float:
        """
        Weighted average of individual ratio scores.
        Each ratio score = pct_of_target clamped to 0–100,
        then scaled by its importance weight.
        """
        if not ratios:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for r in ratios:
            # Extract weight key from ratio name
            key = r.name.lower().replace(" ", "_")
            weight = RATIO_WEIGHTS.get(key, 0.1)
            score  = min(r.pct_of_target, 100.0)  # Cap at 100 for overdeveloped
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        raw_score = weighted_sum / total_weight
        return round(min(max(raw_score, 0.0), 100.0), 1)

    def _compute_symmetry_score(self, ratios: list[RatioResult]) -> float:
        """
        Symmetry score = how consistent the ratio scores are.
        High variance → low symmetry. Perfect uniformity → 100.
        Uses coefficient of variation: lower CV = higher symmetry.
        """
        if len(ratios) < 2:
            return 100.0

        import statistics
        scores = [min(r.pct_of_target, 100.0) for r in ratios]
        mean = statistics.mean(scores)
        if mean == 0:
            return 0.0
        stdev = statistics.stdev(scores)
        cv = stdev / mean  # Coefficient of variation

        # CV of 0 → symmetry 100; CV of 0.5+ → symmetry ~0
        symmetry = max(0.0, 100.0 * (1 - cv * 2))
        return round(symmetry, 1)

    def _classify_areas(
        self, ratios: list[RatioResult]
    ) -> tuple[list[MuscleSummary], list[MuscleSummary]]:
        strong: list[MuscleSummary] = []
        weak:   list[MuscleSummary] = []

        for r in ratios:
            summary = MuscleSummary(
                muscle=r.primary_muscle,
                status=r.status,
                pct_of_target=r.pct_of_target,
            )
            if r.status in (STATUS_OPTIMAL, STATUS_OVERDEVELOPED):
                strong.append(summary)
            else:
                weak.append(summary)

        # Sort weak by pct_of_target ascending (worst first)
        weak.sort(key=lambda x: x.pct_of_target)
        strong.sort(key=lambda x: x.pct_of_target, reverse=True)
        return strong, weak

    def _interpret(
        self,
        score: float,
        lagging: list[str],
        strong: list[MuscleSummary],
    ) -> str:
        label = score_to_label(score)
        lag_str = ", ".join(lagging[:3]) if lagging else "none"
        strength_str = ", ".join(s.muscle for s in strong[:2]) if strong else "balanced"

        if score >= 90:
            return (
                f"Elite physique with near-optimal proportions. "
                f"Strengths: {strength_str}. Minor refinements needed."
            )
        if score >= 75:
            return (
                f"Advanced physique with strong overall development ({label}). "
                f"Prioritise: {lag_str} to elevate your symmetry score."
            )
        if score >= 60:
            return (
                f"Developing physique ({label}). Clear lagging areas in {lag_str}. "
                f"Focused specialisation training will produce significant visual improvements."
            )
        return (
            f"Foundation stage ({label}). Focus on {lag_str} with increased training volume. "
            f"Consistent progressive overload across all muscle groups is the priority."
        )
