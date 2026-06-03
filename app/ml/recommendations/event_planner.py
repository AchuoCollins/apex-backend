"""
app/ml/recommendations/event_planner.py

Event-aware planning helpers.

Given a UserContext that carries an EventContext, derives:
  - training priorities (e.g. ['conditioning', 'strength', 'agility'])
  - weeks remaining bucketed into a training phase
  - recommended weekly volume across priority muscle groups
  - muscle-group emphasis to seed focus areas when the user did not set them
"""
from __future__ import annotations
from dataclasses import dataclass

from app.ml.utils.schemas import UserContext, EventPlanContext


# ── Event-type → training priorities ─────────────────────────────────────────
# Priorities are abstract training qualities, not muscle groups.
EVENT_TYPE_PRIORITIES: dict[str, list[str]] = {
    "bodybuilding_show": ["hypertrophy", "symmetry", "fat_loss"],
    "powerlifting_meet": ["strength", "power", "technique"],
    "photoshoot":        ["aesthetics", "fat_loss", "posture"],
    "wedding":           ["aesthetics", "fat_loss", "conditioning"],
    "vacation":          ["aesthetics", "fat_loss", "conditioning"],
    "athletic_event":    ["conditioning", "strength", "agility"],
    "other":             ["general_fitness", "strength", "conditioning"],
}

# ── Event-type → emphasised muscle groups ────────────────────────────────────
# Used when the user does NOT supply explicit focus areas — gives the
# generator a sensible starting bias for the event.
EVENT_TYPE_MUSCLE_EMPHASIS: dict[str, list[str]] = {
    "bodybuilding_show": ["shoulders", "back", "legs", "arms", "chest"],
    "powerlifting_meet": ["legs", "back", "chest"],
    "photoshoot":        ["shoulders", "chest", "arms", "core"],
    "wedding":           ["shoulders", "arms", "core"],
    "vacation":          ["shoulders", "arms", "core", "legs"],
    "athletic_event":    ["legs", "core", "back", "shoulders"],
    "other":             ["legs", "back", "chest"],
}

# Per-experience baseline weekly volume target across priority groups.
# Used when no event is set.
_BASELINE_WEEKLY_VOLUME = {
    "beginner":     45,
    "intermediate": 70,
    "advanced":     95,
}


@dataclass
class EventPhase:
    name:   str
    notes:  str


def _phase_for_weeks(weeks_remaining: int) -> EventPhase:
    """
    Map weeks-to-event to a training phase.

      >= 12 weeks → foundation     (build base, accumulate volume)
      6–11 weeks  → build          (push intensity, peak volume)
      3–5 weeks   → intensification (drop volume, push load)
      < 3 weeks   → peak / taper   (reduce volume, hold intensity)
    """
    if weeks_remaining >= 12:
        return EventPhase("foundation",     "Accumulation block: prioritise volume and technique.")
    if weeks_remaining >= 6:
        return EventPhase("build",          "Build block: push intensity while sustaining volume.")
    if weeks_remaining >= 3:
        return EventPhase("intensification","Intensification: cut volume ~20%, push working loads.")
    return EventPhase("peak",               "Peak / taper: reduce volume ~40%, hold intensity, sleep & recover.")


def _volume_for_phase(phase: str, level: str) -> int:
    base = _BASELINE_WEEKLY_VOLUME.get(level, _BASELINE_WEEKLY_VOLUME["intermediate"])
    multipliers = {"foundation": 1.10, "build": 1.20, "intensification": 0.95, "peak": 0.60}
    return int(round(base * multipliers.get(phase, 1.0)))


def build_event_plan(context: UserContext) -> EventPlanContext | None:
    """Build an EventPlanContext from the user's event, if present."""
    if not context.is_event_driven or context.event is None:
        return None

    weeks = context.event.weeks_remaining
    phase = _phase_for_weeks(weeks)
    priorities = EVENT_TYPE_PRIORITIES.get(
        context.event.event_type,
        EVENT_TYPE_PRIORITIES["other"],
    )
    weekly_volume = _volume_for_phase(phase.name, context.experience_level)

    return EventPlanContext(
        event_type=context.event.event_type,
        event_name=context.event.event_name,
        weeks_remaining=weeks,
        training_priorities=priorities,
        recommended_weekly_volume=weekly_volume,
        phase=phase.name,
    )


def event_muscle_emphasis(context: UserContext) -> list[str]:
    """
    Muscle groups the event biases the plan toward.
    Returns [] when there is no event.
    """
    if not context.is_event_driven or context.event is None:
        return []
    return list(EVENT_TYPE_MUSCLE_EMPHASIS.get(
        context.event.event_type,
        EVENT_TYPE_MUSCLE_EMPHASIS["other"],
    ))
