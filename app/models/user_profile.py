import enum
from sqlalchemy import String, Integer, Float, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.mixins import TimestampMixin


class FitnessGoal(str, enum.Enum):
    HYPERTROPHY      = "hypertrophy"
    STRENGTH         = "strength"
    FAT_LOSS         = "fat_loss"
    BODY_RECOMPOSITION = "body_recomposition"


class ExperienceLevel(str, enum.Enum):
    BEGINNER     = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED     = "advanced"


class Gender(str, enum.Enum):
    MALE   = "male"
    FEMALE = "female"
    OTHER  = "other"


class TrainingReason(str, enum.Enum):
    GENERAL_FITNESS  = "general_fitness"
    COMPETITION      = "competition"
    EVENT_PREP       = "event_prep"
    HEALTH           = "health"
    AESTHETICS       = "aesthetics"
    PERFORMANCE      = "performance"
    REHABILITATION   = "rehabilitation"


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    fitness_goal: Mapped[FitnessGoal | None] = mapped_column(Enum(FitnessGoal), nullable=True)
    experience_level: Mapped[ExperienceLevel | None] = mapped_column(Enum(ExperienceLevel), nullable=True)
    training_reason: Mapped[TrainingReason | None] = mapped_column(Enum(TrainingReason), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="profile")  # noqa: F821

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} goal={self.fitness_goal}>"
