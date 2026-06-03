from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.event import EventType


class EventBase(BaseModel):
    event_name: str
    event_type: EventType
    event_date: datetime

    @field_validator("event_name")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("event_name cannot be empty")
        if len(v) > 200:
            raise ValueError("event_name too long")
        return v


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    event_name: str | None = None
    event_type: EventType | None = None
    event_date: datetime | None = None


class EventResponse(EventBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
