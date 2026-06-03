from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class FocusAreaCreate(BaseModel):
    focus_area: str

    @field_validator("focus_area")
    @classmethod
    def normalize(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("focus_area cannot be empty")
        if len(v) > 100:
            raise ValueError("focus_area too long")
        return v


class FocusAreaBulkSet(BaseModel):
    focus_areas: list[str]

    @field_validator("focus_areas")
    @classmethod
    def normalize_list(cls, v: list[str]) -> list[str]:
        cleaned = []
        seen = set()
        for item in v:
            s = item.strip().lower()
            if not s or s in seen:
                continue
            if len(s) > 100:
                raise ValueError("focus_area too long")
            seen.add(s)
            cleaned.append(s)
        return cleaned


class FocusAreaResponse(BaseModel):
    id: int
    user_id: int
    focus_area: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
