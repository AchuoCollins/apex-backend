from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.user_profile import FitnessGoal
from app.models.event import EventType
from app.schemas.training import TrainingPlanSummary


class EventCountdown(BaseModel):
    id: int
    event_name: str
    event_type: EventType
    event_date: datetime
    days_remaining: int

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    goal: FitnessGoal | None
    focus_areas: list[str]
    event: EventCountdown | None
    current_training_plan: TrainingPlanSummary | None
