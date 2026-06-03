from sqlalchemy import String, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    profile: Mapped["UserProfile"] = relationship(  # noqa: F821
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    metrics: Mapped[list["BodyMetrics"]] = relationship(  # noqa: F821
        "BodyMetrics", back_populates="user", cascade="all, delete-orphan"
    )
    training_plans: Mapped[list["TrainingPlan"]] = relationship(  # noqa: F821
        "TrainingPlan", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    focus_areas: Mapped[list["UserFocusArea"]] = relationship(  # noqa: F821
        "UserFocusArea", back_populates="user", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
