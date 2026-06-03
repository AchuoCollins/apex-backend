from sqlalchemy import String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.mixins import TimestampMixin


class UserFocusArea(Base, TimestampMixin):
    """A focus area a user wants their training to emphasise (e.g. 'chest', 'glutes')."""
    __tablename__ = "user_focus_areas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    focus_area: Mapped[str] = mapped_column(String(100), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="focus_areas")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("user_id", "focus_area", name="uq_user_focus_area"),
        Index("ix_user_focus_areas_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserFocusArea user_id={self.user_id} focus_area={self.focus_area}>"
