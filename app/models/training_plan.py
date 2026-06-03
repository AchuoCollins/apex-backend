import enum
from sqlalchemy import String, Integer, Float, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.mixins import TimestampMixin
from app.models.user_profile import FitnessGoal, ExperienceLevel


class WorkoutSplit(str, enum.Enum):
    PUSH_PULL_LEGS = "push_pull_legs"
    UPPER_LOWER    = "upper_lower"
    BRO_SPLIT      = "bro_split"
    FULL_BODY      = "full_body"


class TrainingPlan(Base, TimestampMixin):
    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal: Mapped[FitnessGoal] = mapped_column(Enum(FitnessGoal), nullable=False)
    experience_level: Mapped[ExperienceLevel] = mapped_column(Enum(ExperienceLevel), nullable=False)
    workout_split: Mapped[WorkoutSplit] = mapped_column(Enum(WorkoutSplit), nullable=False)
    days_per_week: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    duration_weeks: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # ML hook — reserved for future AI-generated plans
    is_ai_generated: Mapped[bool] = mapped_column(default=False, nullable=False)
    ai_model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="training_plans")  # noqa: F821
    exercises: Mapped[list["TrainingPlanExercise"]] = relationship(
        "TrainingPlanExercise", back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_training_plans_user_active", "user_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<TrainingPlan id={self.id} name={self.name} user_id={self.user_id}>"


class TrainingPlanExercise(Base):
    """Join table — maps exercises to training plans with sets/reps config."""
    __tablename__ = "training_plan_exercises"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)   # 1=Mon … 7=Sun
    order_in_session: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_min: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_max: Mapped[int] = mapped_column(Integer, nullable=False)
    rest_seconds: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    plan: Mapped["TrainingPlan"] = relationship("TrainingPlan", back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="plan_exercises")  # noqa: F821

    __table_args__ = (
        Index("ix_tpe_plan_day", "plan_id", "day_of_week"),
    )
