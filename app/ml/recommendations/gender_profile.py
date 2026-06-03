"""
app/ml/recommendations/gender_profile.py

Gender-aware adjustments for exercise selection, volume, and progression.

The goal here is not to enforce stereotypes but to nudge defaults toward
profiles that match published training literature trends:

  - Females (especially intermediate+) typically respond well to higher lower-body
    frequency (glutes, hamstrings, quads) and benefit from slightly higher reps
    on lower-body work due to higher fatigue resistance.
  - Males more often under-train the posterior chain and over-train chest/arms.

These nudges are *additive* — explicit user focus areas always win.
"""
from __future__ import annotations
from app.ml.utils.schemas import UserContext


# Implicit muscle-group emphasis when no focus areas are set.
_GENDER_EMPHASIS: dict[str, dict[str, list[str]]] = {
    "female": {
        "hypertrophy":         ["glutes", "legs", "back", "shoulders"],
        "strength":            ["legs", "back", "core"],
        "fat_loss":            ["glutes", "legs", "core", "back"],
        "body_recomposition":  ["glutes", "legs", "back", "shoulders"],
    },
    "male": {
        "hypertrophy":         ["back", "shoulders", "legs", "arms"],
        "strength":            ["legs", "back", "chest"],
        "fat_loss":            ["back", "legs", "core", "shoulders"],
        "body_recomposition":  ["back", "legs", "shoulders", "chest"],
    },
    "other": {
        "hypertrophy":         ["back", "shoulders", "legs"],
        "strength":            ["legs", "back", "chest"],
        "fat_loss":            ["back", "legs", "core"],
        "body_recomposition":  ["back", "legs", "shoulders"],
    },
}


# Multiplier on per-exercise set count for compound vs isolation work.
# Conservative — intended only to differentiate two otherwise-identical contexts.
_VOLUME_MULTIPLIERS: dict[str, dict[str, float]] = {
    "female": {"compound": 1.00, "isolation": 1.10},
    "male":   {"compound": 1.05, "isolation": 1.00},
    "other":  {"compound": 1.00, "isolation": 1.00},
}


# Progression cadence guidance (text snippet appended to plan).
_PROGRESSION_NOTES: dict[str, str] = {
    "female": (
        "Female-typical progression: prioritise rep-range mastery (top of range × all sets) "
        "before adding load. Glute and posterior-chain work benefits from higher weekly frequency."
    ),
    "male": (
        "Male-typical progression: linear load progression on compound lifts; "
        "do not neglect posterior-chain (rows, hinges, rear delts) — most common imbalance."
    ),
    "other": (
        "Balanced progression: double progression on compounds, vary rep ranges on isolation work."
    ),
}


def gender_muscle_emphasis(context: UserContext) -> list[str]:
    """Implicit muscle-group bias from gender + goal."""
    g = (context.gender or "other").lower()
    return list(_GENDER_EMPHASIS.get(g, _GENDER_EMPHASIS["other"]).get(
        context.goal,
        _GENDER_EMPHASIS["other"]["hypertrophy"],
    ))


def gender_volume_multiplier(context: UserContext, exercise_type: str) -> float:
    g = (context.gender or "other").lower()
    return _VOLUME_MULTIPLIERS.get(g, _VOLUME_MULTIPLIERS["other"]).get(exercise_type, 1.0)


def gender_progression_note(context: UserContext) -> str:
    g = (context.gender or "other").lower()
    return _PROGRESSION_NOTES.get(g, _PROGRESSION_NOTES["other"])
