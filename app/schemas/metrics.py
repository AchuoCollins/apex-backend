from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MetricsCreate(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    chest_cm: float | None = None
    waist_cm: float | None = None
    shoulders_cm: float | None = None
    arms_cm: float | None = None
    forearms_cm: float | None = None
    neck_cm: float | None = None
    thighs_cm: float | None = None
    calves_cm: float | None = None
    hips_cm: float | None = None
    notes: str | None = None


class MetricsUpdate(MetricsCreate):
    pass


class MetricsResponse(MetricsCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricsList(BaseModel):
    items: list[MetricsResponse]
    total: int
    skip: int
    limit: int
