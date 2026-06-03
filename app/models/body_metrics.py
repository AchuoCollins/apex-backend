from sqlalchemy import Float, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.mixins import TimestampMixin


class BodyMetrics(Base, TimestampMixin):
    """
    Stores a single measurement snapshot for a user.
    Multiple records per user = full history.
    """
    __tablename__ = "body_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Baseline ─────────────────────────────────────────
    height_cm: Mapped[float | None]   = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None]   = mapped_column(Float, nullable=True)
    body_fat_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Circumferences (cm) ──────────────────────────────
    chest_cm:     Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm:     Mapped[float | None] = mapped_column(Float, nullable=True)
    shoulders_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    arms_cm:      Mapped[float | None] = mapped_column(Float, nullable=True)
    forearms_cm:  Mapped[float | None] = mapped_column(Float, nullable=True)
    neck_cm:      Mapped[float | None] = mapped_column(Float, nullable=True)
    thighs_cm:    Mapped[float | None] = mapped_column(Float, nullable=True)
    calves_cm:    Mapped[float | None] = mapped_column(Float, nullable=True)
    hips_cm:      Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="metrics")  # noqa: F821

    __table_args__ = (
        Index("ix_body_metrics_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<BodyMetrics id={self.id} user_id={self.user_id}>"
