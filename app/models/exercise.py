import enum
from sqlalchemy import String, Text, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.mixins import TimestampMixin


class MuscleGroup(str, enum.Enum):
    CHEST     = "chest"
    BACK      = "back"
    SHOULDERS = "shoulders"
    BICEPS    = "biceps"
    TRICEPS   = "triceps"
    LEGS      = "legs"
    CALVES    = "calves"
    CORE      = "core"


class Difficulty(str, enum.Enum):
    BEGINNER     = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED     = "advanced"


class Equipment(str, enum.Enum):
    BARBELL    = "barbell"
    DUMBBELL   = "dumbbell"
    CABLE      = "cable"
    MACHINE    = "machine"
    BODYWEIGHT = "bodyweight"
    KETTLEBELL = "kettlebell"
    BAND       = "band"
    OTHER      = "other"


class ExerciseType(str, enum.Enum):
    COMPOUND  = "compound"
    ISOLATION = "isolation"


class Exercise(Base, TimestampMixin):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    muscle_group: Mapped[MuscleGroup] = mapped_column(Enum(MuscleGroup), nullable=False, index=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False)
    equipment: Mapped[Equipment] = mapped_column(Enum(Equipment), nullable=False)
    exercise_type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationship to training plan exercises
    plan_exercises: Mapped[list["TrainingPlanExercise"]] = relationship(  # noqa: F821
        "TrainingPlanExercise", back_populates="exercise"
    )

    __table_args__ = (
        Index("ix_exercises_muscle_difficulty", "muscle_group", "difficulty"),
    )

    def __repr__(self) -> str:
        return f"<Exercise id={self.id} name={self.name} muscle={self.muscle_group}>"
