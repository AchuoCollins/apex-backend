"""
app/ml/recommendations/training_generator.py

Phase 6 — Intelligent Training Plan Generator.

Generates a full weekly training split personalised to:
  - Identified weak muscle groups (from physique analysis)
  - Training goal (hypertrophy / strength / fat_loss / body_recomposition)
  - Experience level (beginner / intermediate / advanced)

The generator automatically adjusts:
  - Days per week
  - Volume per session
  - Split structure (PPL / Upper-Lower / Full Body / Bro Split)
  - Lagging group frequency (appears 2x/week)
"""
from __future__ import annotations

from app.ml.utils.schemas import (
    UserContext, TrainingSession, TrainingPlanResult, ExerciseRecommendation,
)
from app.ml.recommendations.exercise_recommender import EXERCISE_DB, PRESCRIPTIONS
from app.ml.recommendations.event_planner import (
    build_event_plan, event_muscle_emphasis,
)
from app.ml.recommendations.gender_profile import (
    gender_volume_multiplier, gender_progression_note, gender_muscle_emphasis,
)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ── Split Templates ───────────────────────────────────────────────────────────
# Each template is a list of sessions.
# Each session = (label, [muscle_groups])
# "REST" = rest day.

SPLIT_TEMPLATES = {
    ("beginner", "hypertrophy"): {
        "name": "Full Body — 3 Day",
        "split": "full_body",
        "days_per_week": 3,
        "sessions": [
            ("Full Body A",     ["chest", "back", "legs", "shoulders"]),
            ("Rest",            []),
            ("Full Body B",     ["legs", "chest", "back", "arms"]),
            ("Rest",            []),
            ("Full Body C",     ["shoulders", "back", "legs", "core"]),
            ("Rest",            []),
            ("Rest",            []),
        ],
    },
    ("beginner", "strength"): {
        "name": "Full Body Strength — 3 Day",
        "split": "full_body",
        "days_per_week": 3,
        "sessions": [
            ("Strength A",      ["back", "legs", "chest"]),
            ("Rest",            []),
            ("Strength B",      ["chest", "legs", "back"]),
            ("Rest",            []),
            ("Strength C",      ["legs", "back", "chest"]),
            ("Rest",            []),
            ("Rest",            []),
        ],
    },
    ("beginner", "fat_loss"): {
        "name": "Full Body Fat Loss — 3 Day",
        "split": "full_body",
        "days_per_week": 3,
        "sessions": [
            ("Full Body A",     ["chest", "back", "legs", "core"]),
            ("Rest",            []),
            ("Full Body B",     ["shoulders", "back", "legs", "arms"]),
            ("Rest",            []),
            ("Full Body C",     ["chest", "legs", "core", "arms"]),
            ("Rest",            []),
            ("Rest",            []),
        ],
    },
    ("intermediate", "hypertrophy"): {
        "name": "Push / Pull / Legs — 6 Day",
        "split": "push_pull_legs",
        "days_per_week": 6,
        "sessions": [
            ("Push A",          ["chest", "shoulders", "triceps"]),
            ("Pull A",          ["back", "biceps", "forearms"]),
            ("Legs A",          ["legs", "glutes", "calves"]),
            ("Push B",          ["shoulders", "chest", "triceps"]),
            ("Pull B",          ["back", "biceps"]),
            ("Legs B",          ["legs", "calves", "core"]),
            ("Rest",            []),
        ],
    },
    ("intermediate", "strength"): {
        "name": "Upper / Lower — 4 Day",
        "split": "upper_lower",
        "days_per_week": 4,
        "sessions": [
            ("Upper Strength",  ["chest", "back", "shoulders", "arms"]),
            ("Lower Strength",  ["legs", "glutes", "calves", "core"]),
            ("Rest",            []),
            ("Upper Hypertrophy", ["chest", "back", "shoulders", "arms"]),
            ("Lower Hypertrophy", ["legs", "glutes", "calves"]),
            ("Rest",            []),
            ("Rest",            []),
        ],
    },
    ("intermediate", "fat_loss"): {
        "name": "Upper / Lower — 4 Day",
        "split": "upper_lower",
        "days_per_week": 4,
        "sessions": [
            ("Upper A",         ["chest", "back", "shoulders"]),
            ("Lower A",         ["legs", "glutes", "calves", "core"]),
            ("Rest",            []),
            ("Upper B",         ["back", "shoulders", "arms"]),
            ("Lower B",         ["legs", "calves", "core"]),
            ("Rest",            []),
            ("Rest",            []),
        ],
    },
    ("intermediate", "body_recomposition"): {
        "name": "Push / Pull / Legs — 5 Day",
        "split": "push_pull_legs",
        "days_per_week": 5,
        "sessions": [
            ("Push",            ["chest", "shoulders", "triceps"]),
            ("Pull",            ["back", "biceps", "forearms"]),
            ("Legs",            ["legs", "glutes", "calves"]),
            ("Upper",           ["chest", "back", "shoulders", "arms"]),
            ("Lower",           ["legs", "calves", "core"]),
            ("Rest",            []),
            ("Rest",            []),
        ],
    },
    ("advanced", "hypertrophy"): {
        "name": "Push / Pull / Legs — 6 Day (High Volume)",
        "split": "push_pull_legs",
        "days_per_week": 6,
        "sessions": [
            ("Push A",          ["chest", "shoulders", "triceps"]),
            ("Pull A",          ["back", "biceps", "forearms"]),
            ("Legs A",          ["legs", "glutes", "calves"]),
            ("Push B",          ["shoulders", "chest", "triceps"]),
            ("Pull B",          ["back", "biceps"]),
            ("Legs B",          ["legs", "calves", "core"]),
            ("Rest",            []),
        ],
    },
    ("advanced", "strength"): {
        "name": "Bro Split — 5 Day",
        "split": "bro_split",
        "days_per_week": 5,
        "sessions": [
            ("Chest Day",       ["chest", "triceps"]),
            ("Back Day",        ["back", "biceps", "forearms"]),
            ("Shoulder Day",    ["shoulders", "arms"]),
            ("Leg Day",         ["legs", "glutes", "calves"]),
            ("Arms Day",        ["biceps", "triceps", "forearms", "core"]),
            ("Rest",            []),
            ("Rest",            []),
        ],
    },
}


def _get_template(context: UserContext) -> dict:
    key = (context.experience_level, context.goal)
    if key in SPLIT_TEMPLATES:
        return SPLIT_TEMPLATES[key]
    # Fallback
    fallback_key = (context.experience_level, "hypertrophy")
    return SPLIT_TEMPLATES.get(fallback_key, SPLIT_TEMPLATES[("intermediate", "hypertrophy")])


def _build_exercises(
    muscle_groups: list[str],
    weak_muscles: list[str],
    context: UserContext,
    focus_areas: set[str],
    n_per_group: int = 2,
) -> list[ExerciseRecommendation]:
    """Select exercises for a session's muscle groups."""
    goal  = context.goal
    level = context.experience_level
    presc = PRESCRIPTIONS.get(goal, PRESCRIPTIONS["hypertrophy"])

    # Increase sets for lagging groups
    set_multiplier = 1.3 if level == "advanced" else 1.0

    recs: list[ExerciseRecommendation] = []
    seen_names: set[str] = set()

    for muscle in muscle_groups:
        exercises = EXERCISE_DB.get(muscle, [])
        is_weak  = muscle in weak_muscles
        is_focus = muscle in focus_areas

        # Extra exercise slot for weak OR focus-area groups.
        n_ex = min(n_per_group + (1 if (is_weak or is_focus) else 0), len(exercises))

        for ex_def in exercises[:n_ex]:
            if ex_def.name in seen_names:
                continue
            seen_names.add(ex_def.name)

            p = presc[ex_def.exercise_type]
            base_sets = p["sets"]
            if is_weak:
                base_sets = int(round(base_sets * set_multiplier))
            if is_focus:
                base_sets += 1   # +1 set per focus-area exercise

            # Gender-aware nudge on per-set count (±0–10%).
            gender_mult = gender_volume_multiplier(context, ex_def.exercise_type)
            final_sets = max(1, int(round(base_sets * gender_mult)))

            rationale = ex_def.rationale
            if is_focus:
                rationale = f"[Focus area] {rationale}"

            priority = "high" if (is_weak or is_focus) else "medium"

            recs.append(ExerciseRecommendation(
                name=ex_def.name,
                muscle_group=ex_def.muscle_group,
                exercise_type=ex_def.exercise_type,
                equipment=ex_def.equipment,
                sets=final_sets,
                reps_min=p["reps_min"],
                reps_max=p["reps_max"],
                rest_seconds=p["rest_s"],
                weekly_sets=final_sets,
                rationale=rationale,
                priority=priority,
            ))

    return recs


def _estimate_duration(exercises: list[ExerciseRecommendation]) -> int:
    """Rough session duration estimate in minutes."""
    if not exercises:
        return 0
    total_sets = sum(e.sets for e in exercises)
    avg_rest   = sum(e.rest_seconds for e in exercises) / len(exercises)
    # ~45s per set (work) + avg rest
    return int(round((total_sets * (45 + avg_rest)) / 60)) + 10  # +10 warm-up


def _volume_notes(context: UserContext, total_sets: int) -> str:
    level = context.experience_level
    ranges = {"beginner": (30, 50), "intermediate": (50, 80), "advanced": (70, 120)}
    lo, hi = ranges.get(level, (50, 80))
    if total_sets < lo:
        return f"Weekly volume ({total_sets} sets) is below typical {level} range ({lo}–{hi}). Consider adding 1–2 sets per lagging group."
    if total_sets > hi:
        return f"Weekly volume ({total_sets} sets) is high for {level} level. Ensure recovery is adequate and deload every 4–6 weeks."
    return f"Weekly volume ({total_sets} sets) is well-calibrated for {level} level hypertrophy."


def _progression_notes(context: UserContext) -> str:
    notes = {
        "beginner":     "Add 2.5–5kg to compound lifts every 1–2 weeks. Log every session.",
        "intermediate": "Use double progression: hit top of rep range across all sets before adding weight.",
        "advanced":     "Employ periodisation: rotate between accumulation (high volume) and intensification (high load) blocks every 4–6 weeks.",
    }
    base = notes.get(context.experience_level, notes["intermediate"])
    # Append gender-specific progression nuance.
    return f"{base} {gender_progression_note(context)}"


def _resolved_focus_areas(context: UserContext) -> list[str]:
    """
    Final focus areas to act on:
      1. Explicit user focus areas (always win)
      2. Else, event-derived muscle emphasis
      3. Else, gender + goal implicit emphasis
    """
    if context.focus_areas:
        return list(context.focus_areas)
    event_bias = event_muscle_emphasis(context)
    if event_bias:
        return event_bias
    return gender_muscle_emphasis(context)


def _duration_weeks(context: UserContext, default: int = 8) -> int:
    """Plan length: event-aware when an event is present, else default."""
    if context.is_event_driven and context.event is not None:
        weeks = context.event.weeks_remaining
        if weeks > 0:
            return min(max(1, weeks), 24)
    return default


class TrainingGenerator:
    """
    Generates a personalised weekly training plan.

    The plan automatically:
      - Selects the appropriate split for goal + experience
      - Boosts volume for lagging muscle groups
      - Assigns exercises with correct set/rep prescriptions
      - Estimates session duration
    """

    def generate(
        self,
        weak_muscles: list[str],
        context: UserContext,
    ) -> TrainingPlanResult:
        template = _get_template(context)
        sessions_def = template["sessions"]

        # Merge explicit focus areas with any implicit (event/gender) emphasis.
        # User-set focus areas always take precedence; emphasis fills gaps.
        focus_areas = _resolved_focus_areas(context)
        focus_set = {f.lower() for f in focus_areas}

        weekly_sessions: list[TrainingSession] = []
        total_sets = 0

        for day_idx, (session_label, muscle_groups) in enumerate(sessions_def):
            is_rest = not muscle_groups or session_label.lower() == "rest"

            if is_rest:
                session = TrainingSession(
                    day_number=day_idx + 1,
                    day_name=DAY_NAMES[day_idx],
                    session_label="Rest & Recovery",
                    focus_muscles=[],
                    is_rest=True,
                    exercises=[],
                    total_sets=0,
                    estimated_duration_min=0,
                )
            else:
                # Ensure focus muscles also appear in the session when not
                # already targeted — keeps user-selected priorities present.
                effective_muscles = list(muscle_groups)
                for f in focus_set:
                    if f in EXERCISE_DB and f not in effective_muscles:
                        effective_muscles.append(f)

                exercises = _build_exercises(
                    effective_muscles, weak_muscles, context, focus_set,
                )
                session_sets = sum(e.sets for e in exercises)
                total_sets  += session_sets

                session = TrainingSession(
                    day_number=day_idx + 1,
                    day_name=DAY_NAMES[day_idx],
                    session_label=session_label,
                    focus_muscles=effective_muscles,
                    is_rest=False,
                    exercises=exercises,
                    total_sets=session_sets,
                    estimated_duration_min=_estimate_duration(exercises),
                )

            weekly_sessions.append(session)

        # Event-aware plan context (None if no event).
        event_plan = build_event_plan(context)

        # Plan name
        weak_str  = " + ".join(w.title() for w in weak_muscles[:2])
        plan_name = (
            f"{template['name']} — {context.goal.replace('_', ' ').title()} "
            f"({context.experience_level.title()})"
            + (f" | Priority: {weak_str}" if weak_str else "")
        )
        if focus_areas:
            plan_name += f" | Focus: {', '.join(focus_areas[:3])}"
        if event_plan is not None:
            plan_name += f" | Event: {event_plan.event_type} ({event_plan.weeks_remaining}w)"

        volume_notes = _volume_notes(context, total_sets)
        if event_plan is not None:
            volume_notes += (
                f" Event phase: {event_plan.phase} "
                f"(target ~{event_plan.recommended_weekly_volume} sets/week across priority groups). "
                f"Priorities: {', '.join(event_plan.training_priorities)}."
            )

        gender_note = None
        if context.gender:
            gender_note = (
                f"Profile: {context.gender}. "
                f"{gender_progression_note(context)}"
            )

        return TrainingPlanResult(
            plan_name=plan_name,
            goal=context.goal,
            experience_level=context.experience_level,
            workout_split=template["split"],
            days_per_week=template["days_per_week"],
            duration_weeks=_duration_weeks(context),
            weekly_schedule=weekly_sessions,
            total_weekly_sets=total_sets,
            volume_notes=volume_notes,
            progression_notes=_progression_notes(context),
            is_ai_generated=True,
            focus_areas=focus_areas,
            event_plan=event_plan,
            gender_notes=gender_note,
        )
