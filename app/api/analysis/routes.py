"""
app/api/analysis/routes.py

Phase 8 — FastAPI Analysis Endpoints.

POST /api/analysis/analyze        → Full pipeline (recommended)
POST /api/analysis/physique       → Physique analysis only
POST /api/analysis/predict        → ML weak-point prediction only
POST /api/analysis/recommend      → Exercise recommendations only
POST /api/analysis/training-plan  → Training plan only
"""
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.ml.prediction.prediction_service import PredictionService
from app.ml.utils.schemas import AnalysisRequest
from app.api.analysis.schemas import (
    AnalyzeRequest, PredictRequest, RecommendRequest, TrainingPlanRequest,
    PhysiqueAnalysisResult, DecisionTreeResult,
    RecommendationResult, TrainingPlanResult, FullAnalysisResult,
)

router = APIRouter(prefix="/analysis", tags=["ML Analysis"])


def _service() -> PredictionService:
    """Dependency — returns a PredictionService instance."""
    return PredictionService()


@router.post(
    "/analyze",
    response_model=FullAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Run full ML analysis pipeline",
    description=(
        "Runs all 6 ML phases in sequence: physique analysis → rule engine → "
        "decision tree → exercise recommendations → training plan. "
        "Returns a comprehensive personalised report."
    ),
)
async def full_analysis(
    body: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(_service),
) -> FullAnalysisResult:
    request = AnalysisRequest(measurements=body.measurements, context=body.context)
    return service.full_analysis(request)


@router.post(
    "/physique",
    response_model=PhysiqueAnalysisResult,
    summary="Physique ratio analysis only",
    description="Calculates all aesthetic ratios, physique score, symmetry score, and identifies strong/weak areas.",
)
async def analyze_physique(
    body: PredictRequest,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(_service),
) -> PhysiqueAnalysisResult:
    return service.analyze_physique(body.measurements)


@router.post(
    "/predict",
    response_model=DecisionTreeResult,
    summary="ML weak-point prediction (Decision Tree)",
    description="Uses the trained Decision Tree classifier to predict which muscle group needs the most focus.",
)
async def predict_weak_points(
    body: PredictRequest,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(_service),
) -> DecisionTreeResult:
    return service.predict_weak_points(body.measurements)


@router.post(
    "/recommend",
    response_model=RecommendationResult,
    summary="Exercise recommendations for weak muscle groups",
    description="Maps identified weak muscle groups to evidence-based exercise prescriptions with sets, reps, rest, and frequency.",
)
async def recommend_exercises(
    body: RecommendRequest,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(_service),
) -> RecommendationResult:
    return service.recommend_exercises(body.weak_muscles, body.context)


@router.post(
    "/training-plan",
    response_model=TrainingPlanResult,
    status_code=status.HTTP_201_CREATED,
    summary="Generate personalised training plan",
    description="Generates a full weekly training split based on weak muscle groups, goal, and experience level.",
)
async def generate_training_plan(
    body: TrainingPlanRequest,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(_service),
) -> TrainingPlanResult:
    return service.generate_training_plan(body.weak_muscles, body.context)
