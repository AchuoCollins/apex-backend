import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
from app.models.mixins import TimestampMixin


class EventType(str, enum.Enum):
    BODYBUILDING_SHOW = "bodybuilding_show"
    POWERLIFTING_MEET = "powerlifting_meet"
    PHOTOSHOOT        = "photoshoot"
    WEDDING           = "wedding"
    VACATION          = "vacation"
    ATHLETIC_EVENT    = "athletic_event"
    OTHER             = "other"


class Event(Base, TimestampMixin):
    """A user-defined event (e.g. competition, photoshoot) used to anchor training."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="events")  # noqa: F821

    __table_args__ = (
        Index("ix_events_user_date", "user_id", "event_date"),
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} user_id={self.user_id} name={self.event_name}>"
