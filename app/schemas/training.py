from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.user_profile import FitnessGoal, ExperienceLevel, Gender, TrainingReason
from app.models.training_plan import WorkoutSplit
from app.models.event import EventType
from app.schemas.exercise import ExerciseResponse


class PlanExerciseCreate(BaseModel):
    exercise_id: int
    day_of_week: int
    order_in_session: int = 1
    sets: int
    reps_min: int
    reps_max: int
    rest_seconds: int = 90
    weight_kg: float | None = None
    notes: str | None = None

    @field_validator("day_of_week")
    @classmethod
    def valid_day(cls, v: int) -> int:
        if not 1 <= v <= 7:
            raise ValueError("day_of_week must be between 1 (Mon) and 7 (Sun)")
        return v


class PlanExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    day_of_week: int
    order_in_session: int
    sets: int
    reps_min: int
    reps_max: int
    rest_seconds: int
    weight_kg: float | None
    notes: str | None
    exercise: ExerciseResponse

    model_config = ConfigDict(from_attributes=True)


class TrainingPlanCreate(BaseModel):
    name: str
    description: str | None = None
    goal: FitnessGoal
    experience_level: ExperienceLevel
    workout_split: WorkoutSplit
    days_per_week: int = 4
    duration_weeks: int = 8
    exercises: list[PlanExerciseCreate] = []


class TrainingPlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    goal: FitnessGoal | None = None
    experience_level: ExperienceLevel | None = None
    workout_split: WorkoutSplit | None = None
    days_per_week: int | None = None
    duration_weeks: int | None = None
    is_active: bool | None = None


class TrainingPlanResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None
    goal: FitnessGoal
    experience_level: ExperienceLevel
    workout_split: WorkoutSplit
    days_per_week: int
    duration_weeks: int
    is_active: bool
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime
    exercises: list[PlanExerciseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TrainingPlanGenerateRequest(BaseModel):
    """Advanced inputs for AI-style training plan generation."""
    goal: FitnessGoal
    experience_level: ExperienceLevel
    gender: Gender | None = None
    training_reason: TrainingReason | None = None
    focus_areas: list[str] = []
    workout_split: WorkoutSplit | None = None
    event_type: EventType | None = None
    event_date: datetime | None = None

    @field_validator("focus_areas")
    @classmethod
    def normalize_focus(cls, v: list[str]) -> list[str]:
        seen = set()
        out: list[str] = []
        for s in v:
            t = s.strip().lower()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out


class TrainingPlanSummary(BaseModel):
    id: int
    name: str
    goal: FitnessGoal
    experience_level: ExperienceLevel
    workout_split: WorkoutSplit
    days_per_week: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
