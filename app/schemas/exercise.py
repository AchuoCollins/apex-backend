from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.exercise import MuscleGroup, Difficulty, Equipment, ExerciseType


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: MuscleGroup
    difficulty: Difficulty
    equipment: Equipment
    exercise_type: ExerciseType
    description: str | None = None
    video_url: str | None = None


class ExerciseUpdate(BaseModel):
    name: str | None = None
    muscle_group: MuscleGroup | None = None
    difficulty: Difficulty | None = None
    equipment: Equipment | None = None
    exercise_type: ExerciseType | None = None
    description: str | None = None
    video_url: str | None = None
    is_active: bool | None = None


class ExerciseResponse(BaseModel):
    id: int
    name: str
    muscle_group: MuscleGroup
    difficulty: Difficulty
    equipment: Equipment
    exercise_type: ExerciseType
    description: str | None
    video_url: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExerciseFilter(BaseModel):
    muscle_group: MuscleGroup | None = None
    difficulty: Difficulty | None = None
    equipment: Equipment | None = None
    exercise_type: ExerciseType | None = None
