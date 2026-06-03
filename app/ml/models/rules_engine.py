"""
app/ml/models/rules_engine.py

Phase 2 — Rule-Based Expert System.

Fires conditional sports science rules against a physique analysis result
and generates human-readable coaching insights.

Architecture:
  - Each Rule is a dataclass with an evaluate() method
  - RulesEngine collects all rules and fires them against the analysis
  - Fired rules generate RuleInsight objects
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from app.ml.utils.schemas import (
    PhysiqueAnalysisResult, RuleEngineResult, RuleInsight, UserContext,
)
from app.ml.utils.constants import (
    STATUS_LAGGING, STATUS_DEVELOPING, STATUS_OPTIMAL,
    PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
)


@dataclass
class Rule:
    rule_id:    str
    category:   str
    priority:   str
    title:      str
    condition:  Callable[[PhysiqueAnalysisResult, UserContext], bool]
    explanation: Callable[[PhysiqueAnalysisResult, UserContext], str]
    action:     str


def _ratio_pct(analysis: PhysiqueAnalysisResult, ratio_name_fragment: str) -> float | None:
    """Helper — find a ratio by partial name and return its pct_of_target."""
    for r in analysis.ratios:
        if ratio_name_fragment.lower() in r.name.lower():
            return r.pct_of_target
    return None


def _ratio_status(analysis: PhysiqueAnalysisResult, ratio_name_fragment: str) -> str | None:
    for r in analysis.ratios:
        if ratio_name_fragment.lower() in r.name.lower():
            return r.status
    return None


# ── Rule Definitions ─────────────────────────────────────────────────────────

ALL_RULES: list[Rule] = [

    # ── Proportion Rules ──────────────────────────────────────────────────────

    Rule(
        rule_id="PROP_001",
        category="proportion",
        priority=PRIORITY_HIGH,
        title="Shoulder Width Deficit",
        condition=lambda a, _: (_ratio_pct(a, "Shoulder") or 100) < 85,
        explanation=lambda a, _: (
            f"Your Shoulder-to-Waist ratio is at "
            f"{_ratio_pct(a, 'Shoulder'):.1f}% of the Golden Ratio target (1.618). "
            "Wide shoulders are the single biggest driver of an aesthetic physique. "
            "Shoulder specialisation is your highest priority."
        ),
        action="Add 2–3 dedicated shoulder sessions per week. Prioritise Overhead Press, Lateral Raises, and Face Pulls.",
    ),

    Rule(
        rule_id="PROP_002",
        category="proportion",
        priority=PRIORITY_HIGH,
        title="Arm Development Lagging",
        condition=lambda a, _: (_ratio_pct(a, "Arm To Neck") or 100) < 85,
        explanation=lambda a, _: (
            f"Your Arm-to-Neck ratio is at {_ratio_pct(a, 'Arm To Neck'):.1f}% of target. "
            "Your upper arm circumference should approximately match your neck circumference. "
            "This is one of the most visually impactful ratios for upper body aesthetics."
        ),
        action="Add direct arm work: 4–6 sets of curls and 4–6 sets of tricep extensions per week.",
    ),

    Rule(
        rule_id="PROP_003",
        category="proportion",
        priority=PRIORITY_HIGH,
        title="Calf Development Lagging",
        condition=lambda a, _: (_ratio_pct(a, "Calf To Thigh") or 100) < 80,
        explanation=lambda a, _: (
            f"Calf-to-Thigh ratio at {_ratio_pct(a, 'Calf To Thigh'):.1f}% of target. "
            "Calves are one of the most commonly under-trained muscle groups and create significant "
            "visual imbalance when underdeveloped relative to the thighs."
        ),
        action="Train calves 4–5x/week. Standing and seated calf raises, 4 sets each. Full stretch at bottom — no bouncing.",
    ),

    Rule(
        rule_id="PROP_004",
        category="proportion",
        priority=PRIORITY_MEDIUM,
        title="Chest Development Below Target",
        condition=lambda a, _: (_ratio_pct(a, "Chest To Waist") or 100) < 90,
        explanation=lambda a, _: (
            f"Chest-to-Waist ratio at {_ratio_pct(a, 'Chest To Waist'):.1f}% of the 1.40 target. "
            "A fuller chest dramatically improves the perceived V-taper and overall upper body mass."
        ),
        action="Prioritise incline pressing for upper chest. Add cable flyes for upper chest stretch. 3–4 chest sessions per fortnight.",
    ),

    Rule(
        rule_id="PROP_005",
        category="proportion",
        priority=PRIORITY_MEDIUM,
        title="Leg Development Deficit",
        condition=lambda a, _: (_ratio_pct(a, "Thigh To Waist") or 100) < 85,
        explanation=lambda a, _: (
            f"Thigh-to-Waist ratio at {_ratio_pct(a, 'Thigh To Waist'):.1f}% of target. "
            "Underdeveloped legs create a top-heavy imbalance and are a common symptom of "
            "'skipping leg day.' Prioritising legs will improve your overall symmetry score."
        ),
        action="2 dedicated leg sessions per week. Back squats + Romanian deadlifts as primary movements.",
    ),

    Rule(
        rule_id="PROP_006",
        category="proportion",
        priority=PRIORITY_MEDIUM,
        title="Hip-to-Waist Below X-Frame Target",
        condition=lambda a, _: (_ratio_pct(a, "Hip To Waist") or 100) < 88,
        explanation=lambda a, _: (
            f"Hip-to-Waist ratio at {_ratio_pct(a, 'Hip To Waist'):.1f}% of the 1.25 target. "
            "A wider hip measurement relative to waist creates the athletic X-frame silhouette. "
            "Glute and hip development is key."
        ),
        action="Prioritise hip thrusts, Bulgarian split squats, and Romanian deadlifts to develop glute width.",
    ),

    # ── Volume & Frequency Rules ──────────────────────────────────────────────

    Rule(
        rule_id="VOL_001",
        category="volume",
        priority=PRIORITY_HIGH,
        title="Multiple Lagging Groups — High Volume Redistribution Required",
        condition=lambda a, _: len(a.lagging_groups) >= 3,
        explanation=lambda a, _: (
            f"You have {len(a.lagging_groups)} lagging muscle groups: "
            f"{', '.join(a.lagging_groups[:4])}. "
            "This indicates either insufficient training volume or highly uneven programme design. "
            "A full restructure of your training split is recommended."
        ),
        action="Rebuild your training split with lagging groups appearing 2x per week. Reduce volume on strong areas temporarily.",
    ),

    Rule(
        rule_id="VOL_002",
        category="volume",
        priority=PRIORITY_MEDIUM,
        title="Prioritise Progressive Overload",
        condition=lambda a, ctx: ctx.experience_level == "beginner" and a.physique_score < 60,
        explanation=lambda a, _: (
            "As a beginner, the most important training principle is progressive overload — "
            "adding weight or reps every session. No amount of exercise variety will substitute "
            "for consistent progression on the fundamental compound lifts."
        ),
        action="Track your lifts every session. Aim to add 2.5–5kg to compound lifts every 1–2 weeks.",
    ),

    Rule(
        rule_id="VOL_003",
        category="volume",
        priority=PRIORITY_MEDIUM,
        title="Advanced Training Frequency Recommended",
        condition=lambda a, ctx: ctx.experience_level == "advanced" and a.physique_score >= 70,
        explanation=lambda a, _: (
            "At your advanced level, muscle protein synthesis peaks within 24–48 hours after training. "
            "Training each muscle group 2x per week is substantially more effective than 1x per week for hypertrophy."
        ),
        action="Transition to an Upper/Lower or Push/Pull/Legs split training each muscle 2x per week.",
    ),

    # ── Goal-Specific Rules ───────────────────────────────────────────────────

    Rule(
        rule_id="GOAL_001",
        category="goal",
        priority=PRIORITY_MEDIUM,
        title="Hypertrophy: Rep Range Optimisation",
        condition=lambda _, ctx: ctx.goal == "hypertrophy",
        explanation=lambda _, __: (
            "For hypertrophy, the most effective rep range is 6–20 reps taken close to failure. "
            "Research shows that volume (sets × reps × load) is the primary driver of muscle growth, "
            "not any specific rep range. Vary your rep ranges across exercises."
        ),
        action="Use 3–6 sets per exercise. Mix heavy compounds (4–8 reps) with isolation work (10–20 reps). Train close to failure on each set.",
    ),

    Rule(
        rule_id="GOAL_002",
        category="goal",
        priority=PRIORITY_MEDIUM,
        title="Fat Loss: Maintain Training Intensity",
        condition=lambda _, ctx: ctx.goal == "fat_loss",
        explanation=lambda _, __: (
            "During a fat loss phase, the primary goal is to retain muscle mass. "
            "This requires maintaining training intensity and volume. "
            "Reducing weights or sets significantly during a cut leads to muscle loss."
        ),
        action="Maintain your current training weights and volume. Create your calorie deficit through diet, not reduced training.",
    ),

    Rule(
        rule_id="GOAL_003",
        category="goal",
        priority=PRIORITY_LOW,
        title="Excellent Shoulder-to-Waist Ratio",
        condition=lambda a, _: (_ratio_pct(a, "Shoulder") or 0) >= 95,
        explanation=lambda a, _: (
            f"Your Shoulder-to-Waist ratio is at {_ratio_pct(a, 'Shoulder'):.1f}% of target — exceptional. "
            "This is the most aesthetically impactful proportion and you've nailed it. "
            "Maintenance volume is sufficient here; redirect effort to lagging areas."
        ),
        action="Reduce shoulder volume to maintenance (10–12 sets/week). Redirect saved volume to lagging groups.",
    ),

    # ── Symmetry Rules ────────────────────────────────────────────────────────

    Rule(
        rule_id="SYM_001",
        category="symmetry",
        priority=PRIORITY_HIGH,
        title="Low Symmetry Score — Significant Imbalances Present",
        condition=lambda a, _: a.symmetry_score < 60,
        explanation=lambda a, _: (
            f"Your symmetry score of {a.symmetry_score:.0f}/100 indicates significant proportion imbalances. "
            "Some muscle groups are near target while others are significantly behind. "
            "Visual aesthetics depend heavily on proportion balance — this should be your primary focus."
        ),
        action="Prioritise your 2–3 most lagging muscle groups. Add 1–2 extra sets per session for each lagging group.",
    ),
]


class RulesEngine:
    """
    Evaluates all rules against a physique analysis result and user context.
    Returns fired rules as RuleInsight objects sorted by priority.
    """

    _PRIORITY_ORDER = {PRIORITY_HIGH: 0, PRIORITY_MEDIUM: 1, PRIORITY_LOW: 2}

    def evaluate(
        self,
        analysis: PhysiqueAnalysisResult,
        context: UserContext,
    ) -> RuleEngineResult:
        fired: list[RuleInsight] = []

        for rule in ALL_RULES:
            try:
                if rule.condition(analysis, context):
                    fired.append(RuleInsight(
                        rule_id=rule.rule_id,
                        category=rule.category,
                        priority=rule.priority,
                        title=rule.title,
                        explanation=rule.explanation(analysis, context),
                        action=rule.action,
                    ))
            except Exception:
                continue  # Gracefully skip rules that error due to missing data

        # Sort by priority
        fired.sort(key=lambda x: self._PRIORITY_ORDER.get(x.priority, 99))

        # Primary focus = top 3 lagging muscles or rule-driven focus areas
        primary_focus = analysis.lagging_groups[:3] or [
            a.muscle for a in analysis.weak_areas[:3]
        ]

        return RuleEngineResult(
            insights=fired,
            total_rules_fired=len(fired),
            primary_focus=primary_focus,
        )
