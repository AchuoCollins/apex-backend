"""
app/ml/utils/schemas.py

Pydantic schemas for all ML engine inputs, outputs, and intermediate results.
These are the data contracts between the API layer and the ML layer.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


# ── Inputs ────────────────────────────────────────────────────────────────────

class PhysiqueInput(BaseModel):
    """Raw body measurements from the user."""
    height_cm:    Optional[float] = Field(None, gt=100, lt=250, description="Height in cm")
    weight_kg:    Optional[float] = Field(None, gt=30, lt=300,  description="Weight in kg")
    body_fat_pct: Optional[float] = Field(None, ge=3, le=60,    description="Body fat %")
    chest_cm:     Optional[float] = Field(None, gt=50, lt=200)
    waist_cm:     Optional[float] = Field(None, gt=40, lt=200)
    shoulders_cm: Optional[float] = Field(None, gt=60, lt=250)
    arms_cm:      Optional[float] = Field(None, gt=20, lt=80)
    forearms_cm:  Optional[float] = Field(None, gt=15, lt=60)
    neck_cm:      Optional[float] = Field(None, gt=20, lt=70)
    thighs_cm:    Optional[float] = Field(None, gt=30, lt=120)
    calves_cm:    Optional[float] = Field(None, gt=20, lt=80)
    hips_cm:      Optional[float] = Field(None, gt=50, lt=200)
    age:          Optional[int]   = Field(None, ge=16, le=80)
    gender:       Optional[str]   = Field(None, pattern="^(male|female|other)$")


_TRAINING_REASON_PATTERN = (
    "^(general_fitness|competition|event_prep|health|aesthetics|"
    "performance|rehabilitation)$"
)
_EVENT_TYPE_PATTERN = (
    "^(bodybuilding_show|powerlifting_meet|photoshoot|wedding|"
    "vacation|athletic_event|other)$"
)


class EventContext(BaseModel):
    """Upcoming event that anchors training priorities and timeline."""
    event_type: str = Field(..., pattern=_EVENT_TYPE_PATTERN)
    event_date: datetime
    event_name: Optional[str] = None

    @property
    def weeks_remaining(self) -> int:
        now = datetime.now(timezone.utc)
        target = self.event_date if self.event_date.tzinfo else self.event_date.replace(tzinfo=timezone.utc)
        days = (target - now).days
        return max(0, days // 7)

    @property
    def days_remaining(self) -> int:
        now = datetime.now(timezone.utc)
        target = self.event_date if self.event_date.tzinfo else self.event_date.replace(tzinfo=timezone.utc)
        return max(0, (target - now).days)


class UserContext(BaseModel):
    """
    User profile context for personalising recommendations.

    `goal` and `experience_level` remain required for backward compatibility
    with existing ML callers. The additional profile fields (gender, age,
    height, weight, training_reason, focus_areas) and the optional event
    block are consumed by the recommendation engine when present.
    """
    goal:             str = Field(..., pattern="^(hypertrophy|strength|fat_loss|body_recomposition)$")
    experience_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")

    gender:    Optional[str]   = Field(None, pattern="^(male|female|other)$")
    age:       Optional[int]   = Field(None, ge=12, le=90)
    height_cm: Optional[float] = Field(None, gt=100, lt=250)
    weight_kg: Optional[float] = Field(None, gt=30,  lt=300)

    training_reason: Optional[str] = Field(None, pattern=_TRAINING_REASON_PATTERN)
    focus_areas:     list[str]     = Field(default_factory=list)

    event: Optional[EventContext] = None

    @field_validator("focus_areas")
    @classmethod
    def _normalise_focus(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for s in v:
            t = s.strip().lower()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out

    @property
    def is_event_driven(self) -> bool:
        return self.event is not None


class AnalysisRequest(BaseModel):
    """Combined analysis request."""
    measurements: PhysiqueInput
    context:      UserContext


# ── Ratio Results ─────────────────────────────────────────────────────────────

class RatioResult(BaseModel):
    name:           str
    current:        float
    target:         float
    pct_of_target:  float
    status:         str   # optimal | developing | lagging | overdeveloped
    diff:           float # current - target
    primary_muscle: str
    priority:       str   # high | medium | low

    model_config = ConfigDict(from_attributes=True)


# ── Physique Analysis Output ──────────────────────────────────────────────────

class MuscleSummary(BaseModel):
    muscle:      str
    status:      str
    pct_of_target: float


class PhysiqueAnalysisResult(BaseModel):
    physique_score:    float = Field(..., ge=0, le=100)
    symmetry_score:    float = Field(..., ge=0, le=100)
    grade:             str
    label:             str
    bmi:               Optional[float] = None
    ffmi:              Optional[float] = None
    ratios:            list[RatioResult]
    strong_areas:      list[MuscleSummary]
    weak_areas:        list[MuscleSummary]
    lagging_groups:    list[str]
    data_completeness: float = Field(..., description="0–100% of fields filled")
    interpretation:    str


# ── Rule Engine Output ────────────────────────────────────────────────────────

class RuleInsight(BaseModel):
    rule_id:     str
    category:    str   # proportion | volume | frequency | nutrition
    priority:    str   # high | medium | low
    title:       str
    explanation: str
    action:      str


class RuleEngineResult(BaseModel):
    insights:         list[RuleInsight]
    total_rules_fired: int
    primary_focus:    list[str]   # top 3 muscle groups to prioritise


# ── Decision Tree Output ──────────────────────────────────────────────────────

class WeakPointPrediction(BaseModel):
    muscle_group:    str
    confidence:      float = Field(..., ge=0, le=1)
    is_primary_focus: bool


class DecisionTreeResult(BaseModel):
    predictions:     list[WeakPointPrediction]
    model_version:   str
    top_focus:       str
    feature_importance: dict[str, float]


# ── Exercise Recommendation ───────────────────────────────────────────────────

class ExerciseRecommendation(BaseModel):
    name:          str
    muscle_group:  str
    exercise_type: str     # compound | isolation
    equipment:     str
    sets:          int
    reps_min:      int
    reps_max:      int
    rest_seconds:  int
    weekly_sets:   int
    rationale:     str
    priority:      str


class RecommendationResult(BaseModel):
    weak_muscles:         list[str]
    recommendations:      list[ExerciseRecommendation]
    total_weekly_sets:    int
    estimated_sessions:   int


# ── Training Plan Output ──────────────────────────────────────────────────────

class TrainingSession(BaseModel):
    day_number:    int
    day_name:      str
    session_label: str
    focus_muscles: list[str]
    is_rest:       bool
    exercises:     list[ExerciseRecommendation]
    total_sets:    int
    estimated_duration_min: int


class EventPlanContext(BaseModel):
    """Event-aware metadata included in a generated plan when an event is set."""
    event_type:             str
    event_name:             Optional[str] = None
    weeks_remaining:        int
    training_priorities:    list[str]
    recommended_weekly_volume: int   # target weekly sets across all priority groups
    phase:                  str      # 'foundation' | 'build' | 'intensification' | 'peak'


class TrainingPlanResult(BaseModel):
    plan_name:        str
    goal:             str
    experience_level: str
    workout_split:    str
    days_per_week:    int
    duration_weeks:   int
    weekly_schedule:  list[TrainingSession]
    total_weekly_sets: int
    volume_notes:     str
    progression_notes: str
    is_ai_generated:  bool = True
    focus_areas:      list[str] = Field(default_factory=list)
    event_plan:       Optional[EventPlanContext] = None
    gender_notes:     Optional[str] = None


# ── Full Pipeline Output ──────────────────────────────────────────────────────

class FullAnalysisResult(BaseModel):
    physique_analysis: PhysiqueAnalysisResult
    rule_insights:     RuleEngineResult
    ml_prediction:     Optional[DecisionTreeResult] = None
    recommendations:   RecommendationResult
    training_plan:     TrainingPlanResult
