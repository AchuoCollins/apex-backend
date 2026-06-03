"""
app/api/analysis/schemas.py

Request/response schemas for the /api/analysis endpoints.
Wraps ML schemas in FastAPI-friendly Pydantic models.
"""
from pydantic import BaseModel, Field
from app.ml.utils.schemas import (
    PhysiqueInput, UserContext,
    PhysiqueAnalysisResult, RuleEngineResult,
    DecisionTreeResult, RecommendationResult,
    TrainingPlanResult, FullAnalysisResult,
)


class AnalyzeRequest(BaseModel):
    measurements: PhysiqueInput
    context: UserContext

    model_config = {
        "json_schema_extra": {
            "example": {
                "measurements": {
                    "height_cm": 178,
                    "weight_kg": 82,
                    "body_fat_pct": 15,
                    "chest_cm": 100,
                    "waist_cm": 78,
                    "shoulders_cm": 122,
                    "arms_cm": 36,
                    "forearms_cm": 29,
                    "neck_cm": 38,
                    "thighs_cm": 58,
                    "calves_cm": 36,
                    "hips_cm": 96,
                    "age": 28,
                    "gender": "male",
                },
                "context": {
                    "goal": "hypertrophy",
                    "experience_level": "intermediate",
                    "gender": "male",
                    "age": 28,
                    "height_cm": 178,
                    "weight_kg": 82,
                    "training_reason": "event_prep",
                    "focus_areas": ["chest", "shoulders", "core"],
                    "event": {
                        "event_type": "bodybuilding_show",
                        "event_date": "2026-09-15T00:00:00Z",
                        "event_name": "Autumn Classic"
                    }
                },
            }
        }
    }


class PredictRequest(BaseModel):
    measurements: PhysiqueInput


class RecommendRequest(BaseModel):
    weak_muscles: list[str] = Field(..., min_length=1, max_length=7)
    context: UserContext


class TrainingPlanRequest(BaseModel):
    weak_muscles: list[str] = Field(..., min_length=1, max_length=7)
    context: UserContext


# Re-export response types for use in route declarations
__all__ = [
    "AnalyzeRequest", "PredictRequest", "RecommendRequest", "TrainingPlanRequest",
    "PhysiqueAnalysisResult", "DecisionTreeResult",
    "RecommendationResult", "TrainingPlanResult", "FullAnalysisResult",
]
