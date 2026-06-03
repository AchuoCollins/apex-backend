"""
app/ml/recommendations/exercise_recommender.py

Phase 5 — Exercise Recommendation Engine.

Maps identified weak muscle groups to evidence-based exercise prescriptions.
Returns sets, reps, rest, weekly frequency, and training rationale.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from app.ml.utils.schemas import (
    ExerciseRecommendation, RecommendationResult, UserContext,
)
from app.ml.utils.constants import VOLUME_TARGETS, PRIORITY_HIGH, PRIORITY_MEDIUM
from app.ml.recommendations.gender_profile import gender_volume_multiplier


@dataclass
class ExerciseDef:
    name:          str
    muscle_group:  str
    exercise_type: str   # compound | isolation
    equipment:     str
    rationale:     str


# ── Exercise Database ─────────────────────────────────────────────────────────
# Each muscle group has: primary compound lifts → secondary compounds → isolations

EXERCISE_DB: dict[str, list[ExerciseDef]] = {

    "shoulders": [
        ExerciseDef("Overhead Press",        "shoulders", "compound",  "barbell",  "Primary shoulder mass builder — highest mechanical tension for all three deltoid heads."),
        ExerciseDef("Dumbbell Shoulder Press","shoulders", "compound",  "dumbbell", "Independent arm movement allows greater range of motion and corrects side-to-side imbalances."),
        ExerciseDef("Lateral Raise",          "shoulders", "isolation", "dumbbell", "Directly targets the medial deltoid — the muscle responsible for shoulder width."),
        ExerciseDef("Face Pull",              "shoulders", "isolation", "cable",    "Rear delt and external rotator health — critical for shoulder balance and injury prevention."),
        ExerciseDef("Cable Lateral Raise",    "shoulders", "isolation", "cable",    "Constant cable tension provides superior stimulus vs dumbbell variation in shortened position."),
    ],

    "chest": [
        ExerciseDef("Incline Barbell Press",  "chest", "compound",  "barbell",  "Upper chest priority — the most underdeveloped region and most aesthetically impactful."),
        ExerciseDef("Flat Barbell Bench Press","chest", "compound",  "barbell",  "Highest load compound press — best for overall chest mass and strength."),
        ExerciseDef("Incline Dumbbell Press", "chest", "compound",  "dumbbell", "Upper chest with greater stretch and independent arm movement."),
        ExerciseDef("Cable Crossover",        "chest", "isolation", "cable",    "Peak contraction isolation — trains the chest in the shortened position."),
        ExerciseDef("Pec Deck / Flye",        "chest", "isolation", "machine",  "Constant tension isolation — excellent for hypertrophy when taken close to failure."),
    ],

    "arms": [
        ExerciseDef("Barbell Curl",           "biceps",  "isolation", "barbell",  "Highest load bicep exercise — primary mass builder."),
        ExerciseDef("Incline Dumbbell Curl",  "biceps",  "isolation", "dumbbell", "Long head stretch position — critical for bicep peak development."),
        ExerciseDef("Hammer Curl",            "biceps",  "isolation", "dumbbell", "Brachialis and brachioradialis — adds arm thickness and forearm development."),
        ExerciseDef("Close-Grip Bench Press", "triceps", "compound",  "barbell",  "Best tricep mass builder — medial and lateral head primary movers."),
        ExerciseDef("Overhead Tricep Ext",    "triceps", "isolation", "dumbbell", "Long head stretch — the largest tricep head and most underdeveloped in most people."),
        ExerciseDef("Cable Pushdown",         "triceps", "isolation", "cable",    "Constant tension lateral head isolation — finisher exercise."),
    ],

    "biceps": [
        ExerciseDef("Barbell Curl",           "biceps",  "isolation", "barbell",  "Primary bilateral bicep mass builder."),
        ExerciseDef("Incline Dumbbell Curl",  "biceps",  "isolation", "dumbbell", "Long head stretch for peak development."),
        ExerciseDef("Hammer Curl",            "biceps",  "isolation", "dumbbell", "Brachialis thickness."),
        ExerciseDef("Cable Curl",             "biceps",  "isolation", "cable",    "Constant tension — excellent as a finisher."),
    ],

    "triceps": [
        ExerciseDef("Close-Grip Bench Press", "triceps", "compound",  "barbell",  "Mass builder."),
        ExerciseDef("Overhead Tricep Ext",    "triceps", "isolation", "dumbbell", "Long head stretch."),
        ExerciseDef("Cable Pushdown",         "triceps", "isolation", "cable",    "Lateral head finisher."),
        ExerciseDef("Skull Crusher",          "triceps", "isolation", "barbell",  "Long head with more load than dumbbell variation."),
    ],

    "back": [
        ExerciseDef("Weighted Pull-Up",       "back", "compound",  "bodyweight", "Best lat width builder — vertical pull with full range of motion."),
        ExerciseDef("Barbell Row",            "back", "compound",  "barbell",    "Primary horizontal pull — upper back thickness and rhomboid development."),
        ExerciseDef("Lat Pulldown",           "back", "compound",  "cable",      "Vertical pull — excellent for lat isolation and beginners who can't do pull-ups yet."),
        ExerciseDef("Seated Cable Row",       "back", "compound",  "cable",      "Horizontal pull with constant cable tension — mid-back thickness."),
        ExerciseDef("Straight-Arm Pulldown",  "back", "isolation", "cable",      "Pure lat isolation through shoulder extension."),
    ],

    "legs": [
        ExerciseDef("Barbell Back Squat",     "legs", "compound",  "barbell",  "King of leg exercises — greatest quad and glute stimulus."),
        ExerciseDef("Romanian Deadlift",      "legs", "compound",  "barbell",  "Hamstring and glute hinge — essential for posterior chain balance."),
        ExerciseDef("Leg Press",              "legs", "compound",  "machine",  "High-load quad and glute compound with reduced spinal loading."),
        ExerciseDef("Leg Curl",               "legs", "isolation", "machine",  "Hamstring isolation — essential for knee health and balanced leg development."),
        ExerciseDef("Bulgarian Split Squat",  "legs", "compound",  "dumbbell", "Unilateral quad and glute — corrects left-right imbalances."),
        ExerciseDef("Leg Extension",          "legs", "isolation", "machine",  "Quad isolation in shortened position — complements squats."),
    ],

    "glutes": [
        ExerciseDef("Hip Thrust",             "glutes", "compound",  "barbell",  "Primary glute builder — highest glute EMG of any exercise."),
        ExerciseDef("Romanian Deadlift",      "glutes", "compound",  "barbell",  "Glute and hamstring hinge — loaded stretch position."),
        ExerciseDef("Bulgarian Split Squat",  "glutes", "compound",  "dumbbell", "Unilateral glute and quad — great for hip width development."),
        ExerciseDef("Cable Pull-Through",     "glutes", "isolation", "cable",    "Glute isolation through hip extension — excellent mind-muscle connection."),
    ],

    "calves": [
        ExerciseDef("Standing Calf Raise",    "calves", "isolation", "machine",  "Primary gastrocnemius builder — do NOT skip the full stretch at bottom."),
        ExerciseDef("Seated Calf Raise",      "calves", "isolation", "machine",  "Soleus emphasis with bent knee — often neglected and adds calf thickness."),
        ExerciseDef("Donkey Calf Raise",      "calves", "isolation", "machine",  "Superior stretch position for gastrocnemius compared to standing variation."),
    ],

    "forearms": [
        ExerciseDef("Barbell Wrist Curl",     "forearms", "isolation", "barbell",  "Direct flexor mass builder."),
        ExerciseDef("Reverse Curl",           "forearms", "isolation", "barbell",  "Brachioradialis and extensor development."),
        ExerciseDef("Farmer's Walk",          "forearms", "compound",  "dumbbell", "Grip strength and forearm hypertrophy simultaneously."),
        ExerciseDef("Dead Hang",              "forearms", "isolation", "bodyweight","Grip endurance and forearm development — easy to add to any session."),
    ],

    "core": [
        ExerciseDef("Ab Wheel Rollout",       "core", "compound",  "other",    "Anti-extension core stability — highest core activation of any exercise."),
        ExerciseDef("Cable Crunch",           "core", "isolation", "cable",    "Weighted crunch — builds actual ab thickness, not just endurance."),
        ExerciseDef("Hanging Leg Raise",      "core", "compound",  "bodyweight","Hip flexor and lower abs through full range."),
        ExerciseDef("Plank",                  "core", "isolation", "bodyweight","Isometric anti-extension — good foundation for beginners."),
    ],
}

# ── Rep/Rest prescriptions by goal ───────────────────────────────────────────

PRESCRIPTIONS = {
    "hypertrophy": {
        "compound":  {"sets": 4, "reps_min": 6,  "reps_max": 12, "rest_s": 120},
        "isolation": {"sets": 3, "reps_min": 10, "reps_max": 20, "rest_s":  75},
    },
    "strength": {
        "compound":  {"sets": 5, "reps_min": 3,  "reps_max": 6,  "rest_s": 240},
        "isolation": {"sets": 3, "reps_min": 8,  "reps_max": 12, "rest_s":  90},
    },
    "fat_loss": {
        "compound":  {"sets": 3, "reps_min": 10, "reps_max": 15, "rest_s":  60},
        "isolation": {"sets": 3, "reps_min": 12, "reps_max": 20, "rest_s":  45},
    },
    "body_recomposition": {
        "compound":  {"sets": 4, "reps_min": 8,  "reps_max": 12, "rest_s":  90},
        "isolation": {"sets": 3, "reps_min": 12, "reps_max": 15, "rest_s":  60},
    },
}

WEEKLY_FREQ = {
    "beginner":     {"lagging": 2, "normal": 1},
    "intermediate": {"lagging": 3, "normal": 2},
    "advanced":     {"lagging": 4, "normal": 2},
}


class ExerciseRecommender:
    """
    Selects exercises for each weak muscle group and prescribes
    sets, reps, rest, and weekly frequency based on goal and experience.
    """

    def recommend(
        self,
        weak_muscles: list[str],
        context: UserContext,
    ) -> RecommendationResult:
        goal  = context.goal
        level = context.experience_level
        presc = PRESCRIPTIONS.get(goal, PRESCRIPTIONS["hypertrophy"])
        freq  = WEEKLY_FREQ.get(level, WEEKLY_FREQ["intermediate"])

        focus_set = {f.lower() for f in context.focus_areas}

        all_recs: list[ExerciseRecommendation] = []

        for muscle in weak_muscles[:5]:   # Cap at 5 groups per recommendation
            exercises = EXERCISE_DB.get(muscle, [])
            # Take top 2–3 exercises per muscle group; bump to +1 when the
            # group is an explicit user-selected focus area.
            base_n = 3 if muscle in ["shoulders", "arms", "legs"] else 2
            n_exercises = min(base_n + (1 if muscle in focus_set else 0), len(exercises))
            selected = exercises[:n_exercises]

            is_primary = muscle == weak_muscles[0]
            is_focus   = muscle in focus_set
            priority   = PRIORITY_HIGH if (is_primary or is_focus) else PRIORITY_MEDIUM
            wk_freq    = freq["lagging"] if (is_primary or is_focus) else freq["normal"]

            for ex_def in selected:
                p = presc[ex_def.exercise_type]

                # Focus-area boost: +1 set per session on focused groups.
                base_sets = p["sets"] + (1 if is_focus else 0)
                # Gender-aware nudge on per-set count (typically ±0–10%).
                gender_mult = gender_volume_multiplier(context, ex_def.exercise_type)
                per_session_sets = max(1, int(round(base_sets * gender_mult)))
                weekly_sets = per_session_sets * wk_freq

                rationale = ex_def.rationale
                if is_focus:
                    rationale = f"[Focus area] {rationale}"

                all_recs.append(ExerciseRecommendation(
                    name=ex_def.name,
                    muscle_group=ex_def.muscle_group,
                    exercise_type=ex_def.exercise_type,
                    equipment=ex_def.equipment,
                    sets=per_session_sets,
                    reps_min=p["reps_min"],
                    reps_max=p["reps_max"],
                    rest_seconds=p["rest_s"],
                    weekly_sets=weekly_sets,
                    rationale=rationale,
                    priority=priority,
                ))

        total_weekly = sum(r.weekly_sets for r in all_recs)
        sessions     = min(6, max(3, len(weak_muscles) + 1))

        return RecommendationResult(
            weak_muscles=weak_muscles,
            recommendations=all_recs,
            total_weekly_sets=total_weekly,
            estimated_sessions=sessions,
        )
