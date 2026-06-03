from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.models.training_plan import TrainingPlan, TrainingPlanExercise, WorkoutSplit
from app.models.user_profile import FitnessGoal, ExperienceLevel
from app.repositories.training_repository import TrainingPlanRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.training import (
    TrainingPlanCreate, TrainingPlanUpdate,
    TrainingPlanResponse, TrainingPlanSummary,
    TrainingPlanGenerateRequest,
)

# ── Template definitions ──────────────────────────────────────────────────────
# Format: {goal: {level: {split: [(muscle_group, exercise_name, day, sets, reps_min, reps_max, rest_s)]}}}
# These are predefined — no AI yet. ML layer will override this later.

PLAN_TEMPLATES: dict = {
    FitnessGoal.HYPERTROPHY: {
        ExperienceLevel.BEGINNER: {
            WorkoutSplit.PUSH_PULL_LEGS: [
                # Day 1 — Push
                ("chest",     "Flat Barbell Bench Press",   1, 3, 8, 12, 90),
                ("shoulders", "Dumbbell Shoulder Press",    1, 3, 8, 12, 90),
                ("triceps",   "Cable Tricep Pushdown",      1, 3, 10, 15, 60),
                # Day 2 — Pull
                ("back",      "Lat Pulldown",               2, 3, 8, 12, 90),
                ("biceps",    "Barbell Curl",               2, 3, 10, 12, 60),
                # Day 3 — Legs
                ("legs",      "Barbell Back Squat",         3, 3, 8, 10, 120),
                ("legs",      "Leg Press",                  3, 3, 10, 15, 90),
                ("calves",    "Standing Calf Raise",        3, 3, 12, 15, 60),
            ]
        },
        ExperienceLevel.INTERMEDIATE: {
            WorkoutSplit.PUSH_PULL_LEGS: [
                # Day 1 — Push
                ("chest",     "Incline Barbell Press",      1, 4, 6, 10, 120),
                ("chest",     "Flat Dumbbell Flye",         1, 3, 10, 15, 90),
                ("shoulders", "Overhead Press",             1, 4, 6, 10, 120),
                ("shoulders", "Lateral Raise",              1, 4, 12, 15, 60),
                ("triceps",   "Close-Grip Bench Press",     1, 3, 8, 12, 90),
                ("triceps",   "Overhead Tricep Extension",  1, 3, 10, 15, 60),
                # Day 2 — Pull
                ("back",      "Weighted Pull-Up",           2, 4, 5, 8, 120),
                ("back",      "Barbell Row",                2, 4, 6, 10, 120),
                ("back",      "Seated Cable Row",           2, 3, 10, 15, 90),
                ("biceps",    "Incline Dumbbell Curl",      2, 3, 10, 12, 60),
                ("biceps",    "Hammer Curl",                2, 3, 12, 15, 60),
                # Day 3 — Legs
                ("legs",      "Barbell Back Squat",         3, 4, 5, 8, 180),
                ("legs",      "Romanian Deadlift",          3, 3, 8, 12, 120),
                ("legs",      "Leg Press",                  3, 3, 10, 15, 90),
                ("legs",      "Leg Curl",                   3, 3, 10, 15, 90),
                ("calves",    "Standing Calf Raise",        3, 4, 10, 12, 60),
            ]
        },
        ExperienceLevel.ADVANCED: {
            WorkoutSplit.PUSH_PULL_LEGS: [
                # Day 1 — Push A
                ("chest",     "Incline Barbell Press",      1, 5, 4, 6, 180),
                ("chest",     "Flat Dumbbell Press",        1, 4, 8, 12, 120),
                ("chest",     "Cable Crossover",            1, 3, 12, 15, 60),
                ("shoulders", "Overhead Press",             1, 5, 4, 6, 180),
                ("shoulders", "Lateral Raise",              1, 5, 12, 20, 60),
                ("triceps",   "Close-Grip Bench Press",     1, 4, 6, 10, 120),
                ("triceps",   "Overhead Tricep Extension",  1, 3, 10, 15, 60),
                # Day 2 — Pull A
                ("back",      "Weighted Pull-Up",           2, 5, 4, 6, 180),
                ("back",      "Barbell Row",                2, 4, 6, 8, 150),
                ("back",      "Straight-Arm Pulldown",      2, 3, 12, 15, 60),
                ("biceps",    "Barbell Curl",               2, 4, 6, 10, 90),
                ("biceps",    "Incline Dumbbell Curl",      2, 3, 10, 12, 60),
                # Day 3 — Legs A
                ("legs",      "Barbell Back Squat",         3, 5, 3, 5, 240),
                ("legs",      "Romanian Deadlift",          3, 4, 8, 10, 150),
                ("legs",      "Leg Press",                  3, 3, 10, 15, 90),
                ("legs",      "Leg Curl",                   3, 4, 8, 12, 90),
                ("legs",      "Leg Extension",              3, 3, 12, 15, 60),
                ("calves",    "Standing Calf Raise",        3, 5, 8, 12, 60),
                ("calves",    "Seated Calf Raise",          3, 3, 15, 20, 60),
            ]
        },
    },
    FitnessGoal.STRENGTH: {
        ExperienceLevel.INTERMEDIATE: {
            WorkoutSplit.UPPER_LOWER: [
                # Day 1 — Upper
                ("chest",     "Flat Barbell Bench Press",   1, 5, 3, 5, 180),
                ("back",      "Barbell Row",                1, 5, 3, 5, 180),
                ("shoulders", "Overhead Press",             1, 4, 4, 6, 150),
                ("biceps",    "Barbell Curl",               1, 3, 6, 8, 90),
                # Day 2 — Lower
                ("legs",      "Barbell Back Squat",         2, 5, 3, 5, 240),
                ("legs",      "Romanian Deadlift",          2, 4, 5, 8, 180),
                ("calves",    "Standing Calf Raise",        2, 3, 10, 12, 60),
                # Day 3 — Upper
                ("chest",     "Incline Barbell Press",      3, 4, 4, 6, 180),
                ("back",      "Weighted Pull-Up",           3, 4, 4, 6, 180),
                ("triceps",   "Close-Grip Bench Press",     3, 3, 5, 8, 120),
                # Day 4 — Lower
                ("legs",      "Deadlift",                   4, 5, 1, 5, 300),
                ("legs",      "Leg Press",                  4, 3, 8, 10, 120),
                ("core",      "Ab Wheel Rollout",           4, 3, 8, 12, 60),
            ]
        },
    },
    FitnessGoal.FAT_LOSS: {
        ExperienceLevel.BEGINNER: {
            WorkoutSplit.FULL_BODY: [
                ("chest",     "Push-Up",                    1, 3, 10, 20, 60),
                ("back",      "Dumbbell Row",               1, 3, 10, 15, 60),
                ("legs",      "Goblet Squat",               1, 3, 10, 15, 60),
                ("shoulders", "Dumbbell Shoulder Press",    1, 3, 10, 15, 60),
                ("core",      "Plank",                      1, 3, 20, 30, 45),
                ("chest",     "Push-Up",                    2, 3, 10, 20, 60),
                ("back",      "Lat Pulldown",               2, 3, 10, 15, 60),
                ("legs",      "Romanian Deadlift",          2, 3, 10, 15, 90),
                ("core",      "Cable Crunch",               2, 3, 12, 15, 60),
                ("chest",     "Push-Up",                    3, 3, 10, 20, 60),
                ("legs",      "Leg Press",                  3, 3, 12, 15, 90),
                ("shoulders", "Lateral Raise",              3, 3, 12, 15, 60),
                ("core",      "Ab Wheel Rollout",           3, 3, 8, 12, 60),
            ]
        },
    },
    FitnessGoal.BODY_RECOMPOSITION: {
        ExperienceLevel.INTERMEDIATE: {
            WorkoutSplit.UPPER_LOWER: [
                ("chest",     "Flat Barbell Bench Press",   1, 4, 6, 10, 120),
                ("back",      "Barbell Row",                1, 4, 6, 10, 120),
                ("shoulders", "Overhead Press",             1, 3, 8, 12, 90),
                ("biceps",    "Barbell Curl",               1, 3, 10, 12, 60),
                ("triceps",   "Cable Tricep Pushdown",      1, 3, 10, 15, 60),
                ("legs",      "Barbell Back Squat",         2, 4, 6, 10, 150),
                ("legs",      "Romanian Deadlift",          2, 3, 8, 12, 120),
                ("legs",      "Leg Curl",                   2, 3, 10, 15, 90),
                ("calves",    "Standing Calf Raise",        2, 3, 12, 15, 60),
                ("chest",     "Incline Dumbbell Press",     3, 4, 8, 12, 90),
                ("back",      "Weighted Pull-Up",           3, 4, 5, 8, 120),
                ("shoulders", "Lateral Raise",              3, 4, 12, 15, 60),
                ("biceps",    "Hammer Curl",                3, 3, 10, 12, 60),
                ("legs",      "Leg Press",                  4, 3, 10, 15, 90),
                ("legs",      "Bulgarian Split Squat",      4, 3, 10, 12, 90),
                ("core",      "Cable Crunch",               4, 3, 12, 15, 60),
                ("calves",    "Seated Calf Raise",          4, 3, 15, 20, 60),
            ]
        },
    },
}


class TrainingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TrainingPlanRepository(session)
        self.exercise_repo = ExerciseRepository(session)

    async def get_list(self, user_id: int, skip: int = 0, limit: int = 20) -> list[TrainingPlanSummary]:
        plans = await self.repo.get_by_user(user_id, skip=skip, limit=limit)
        return [TrainingPlanSummary.model_validate(p) for p in plans]

    async def get_by_id(self, plan_id: int, user_id: int) -> TrainingPlanResponse:
        plan = await self.repo.get_by_id_with_exercises(plan_id, user_id)
        if not plan:
            raise NotFoundException("Training plan", plan_id)
        return TrainingPlanResponse.model_validate(plan)

    async def create(self, user_id: int, data: TrainingPlanCreate) -> TrainingPlanResponse:
        plan = TrainingPlan(
            user_id=user_id,
            name=data.name,
            description=data.description,
            goal=data.goal,
            experience_level=data.experience_level,
            workout_split=data.workout_split,
            days_per_week=data.days_per_week,
            duration_weeks=data.duration_weeks,
        )
        plan = await self.repo.create(plan)

        for ex_data in data.exercises:
            plan_ex = TrainingPlanExercise(
                plan_id=plan.id,
                exercise_id=ex_data.exercise_id,
                day_of_week=ex_data.day_of_week,
                order_in_session=ex_data.order_in_session,
                sets=ex_data.sets,
                reps_min=ex_data.reps_min,
                reps_max=ex_data.reps_max,
                rest_seconds=ex_data.rest_seconds,
                weight_kg=ex_data.weight_kg,
                notes=ex_data.notes,
            )
            self.session.add(plan_ex)

        await self.session.flush()
        return await self.get_by_id(plan.id, user_id)

    async def generate_from_template(
        self,
        user_id: int,
        goal: FitnessGoal,
        experience_level: ExperienceLevel,
        workout_split: WorkoutSplit,
    ) -> TrainingPlanResponse:
        """
        Generate a plan from predefined templates.
        Falls back gracefully when no exact template match exists.
        ML service will override this method in a future phase.
        """
        return await self._generate_internal(
            user_id=user_id,
            goal=goal,
            experience_level=experience_level,
            workout_split=workout_split,
            focus_areas=[],
        )

    async def generate(
        self, user_id: int, data: TrainingPlanGenerateRequest
    ) -> TrainingPlanResponse:
        """
        Advanced generation entry-point.
        Uses goal, experience_level, focus_areas, training_reason, gender,
        event_type and event_date to shape a plan.
        """
        workout_split = data.workout_split or self._default_split(
            data.goal, data.experience_level
        )
        duration_weeks = self._duration_weeks_from_event(data.event_date)

        plan_descr_parts = [f"Goal: {data.goal.value.replace('_', ' ')}"]
        if data.training_reason:
            plan_descr_parts.append(f"reason: {data.training_reason.value.replace('_', ' ')}")
        if data.gender:
            plan_descr_parts.append(f"gender: {data.gender.value}")
        if data.focus_areas:
            plan_descr_parts.append(f"focus: {', '.join(data.focus_areas)}")
        if data.event_type and data.event_date:
            plan_descr_parts.append(
                f"event: {data.event_type.value} on {data.event_date.date().isoformat()}"
            )
        description = " | ".join(plan_descr_parts)

        return await self._generate_internal(
            user_id=user_id,
            goal=data.goal,
            experience_level=data.experience_level,
            workout_split=workout_split,
            focus_areas=data.focus_areas,
            duration_weeks=duration_weeks,
            description=description,
        )

    @staticmethod
    def _default_split(goal: FitnessGoal, level: ExperienceLevel) -> WorkoutSplit:
        if level == ExperienceLevel.BEGINNER:
            return WorkoutSplit.FULL_BODY
        if goal == FitnessGoal.STRENGTH:
            return WorkoutSplit.UPPER_LOWER
        if goal == FitnessGoal.FAT_LOSS:
            return WorkoutSplit.FULL_BODY
        return WorkoutSplit.PUSH_PULL_LEGS

    @staticmethod
    def _duration_weeks_from_event(event_date) -> int:
        if not event_date:
            return 8
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        target = event_date if event_date.tzinfo else event_date.replace(tzinfo=timezone.utc)
        weeks = max(1, int((target - now).days // 7))
        return min(weeks, 24)

    async def _generate_internal(
        self,
        *,
        user_id: int,
        goal: FitnessGoal,
        experience_level: ExperienceLevel,
        workout_split: WorkoutSplit,
        focus_areas: list[str],
        duration_weeks: int = 8,
        description: str | None = None,
    ) -> TrainingPlanResponse:
        goal_templates = PLAN_TEMPLATES.get(goal, {})
        level_templates = goal_templates.get(
            experience_level,
            goal_templates.get(ExperienceLevel.INTERMEDIATE, {})
        )
        split_exercises = level_templates.get(
            workout_split,
            next(iter(level_templates.values())) if level_templates else []
        )

        # Boost sets for focus-area muscle groups
        focus_set = {f.lower() for f in focus_areas}

        plan_name = (
            f"{goal.value.replace('_', ' ').title()} — "
            f"{experience_level.value.title()} "
            f"({workout_split.value.replace('_', ' ').title()})"
        )
        if focus_set:
            plan_name += f" | Focus: {', '.join(sorted(focus_set))}"

        plan = TrainingPlan(
            user_id=user_id,
            name=plan_name,
            description=description or f"Template-generated plan for {goal.value.replace('_', ' ')}.",
            goal=goal,
            experience_level=experience_level,
            workout_split=workout_split,
            days_per_week=len({e[2] for e in split_exercises}) if split_exercises else 3,
            duration_weeks=duration_weeks,
            is_ai_generated=bool(focus_set) or description is not None,
        )
        plan = await self.repo.create(plan)

        for order, (muscle_group, ex_name, day, sets, reps_min, reps_max, rest_s) in enumerate(split_exercises, 1):
            exercise = await self.exercise_repo.get_by_name(ex_name)
            if not exercise:
                continue

            boosted_sets = sets + 1 if muscle_group in focus_set else sets

            plan_ex = TrainingPlanExercise(
                plan_id=plan.id,
                exercise_id=exercise.id,
                day_of_week=day,
                order_in_session=order,
                sets=boosted_sets,
                reps_min=reps_min,
                reps_max=reps_max,
                rest_seconds=rest_s,
                notes="Prioritised focus area" if muscle_group in focus_set else None,
            )
            self.session.add(plan_ex)

        await self.session.flush()
        return await self.get_by_id(plan.id, user_id)

    async def update(self, plan_id: int, user_id: int, data: TrainingPlanUpdate) -> TrainingPlanResponse:
        plan = await self.repo.get_plan_for_user(plan_id, user_id)
        if not plan:
            raise NotFoundException("Training plan", plan_id)

        update_data = data.model_dump(exclude_none=True)
        await self.repo.update(plan, **update_data)
        return await self.get_by_id(plan_id, user_id)

    async def delete(self, plan_id: int, user_id: int) -> None:
        plan = await self.repo.get_plan_for_user(plan_id, user_id)
        if not plan:
            raise NotFoundException("Training plan", plan_id)
        await self.repo.delete(plan)
