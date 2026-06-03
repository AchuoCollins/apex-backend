from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.user_profile import FitnessGoal, ExperienceLevel, Gender, TrainingReason


# ── Profile ──────────────────────────────────────────────────────────────────

class UserProfileBase(BaseModel):
    age: int | None = None
    gender: Gender | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    fitness_goal: FitnessGoal | None = None
    experience_level: ExperienceLevel | None = None
    training_reason: TrainingReason | None = None
    bio: str | None = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Focus Areas ──────────────────────────────────────────────────────────────

class FocusAreaResponse(BaseModel):
    id: int
    user_id: int
    focus_area: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── User ─────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    profile: UserProfileResponse | None = None
    focus_areas: list[FocusAreaResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    profile: UserProfileUpdate | None = None


class UserSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)
