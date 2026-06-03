"""
app/ml/prediction/physique_predictor.py

Interface stub for the future ML physique analysis model.
When the ML layer is built, implement this interface and wire it
into TrainingService.generate_from_template().
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.models.user_profile import FitnessGoal, ExperienceLevel
from app.models.training_plan import WorkoutSplit


@dataclass
class PhysiqueAnalysisInput:
    """Input features for the ML model."""
    height_cm: float | None
    weight_kg: float | None
    body_fat_pct: float | None
    shoulders_cm: float | None
    chest_cm: float | None
    waist_cm: float | None
    hips_cm: float | None
    arms_cm: float | None
    thighs_cm: float | None
    calves_cm: float | None
    neck_cm: float | None
    goal: FitnessGoal
    experience_level: ExperienceLevel


@dataclass
class PhysiqueAnalysisOutput:
    """Output from the ML model — lag predictions + recommended split."""
    lagging_muscle_groups: list[str]
    physique_score: float           # 0–100
    recommended_split: WorkoutSplit
    recommended_days_per_week: int
    confidence: float               # 0–1
    model_version: str


class BasePhysiquePredictor(ABC):
    """
    Abstract predictor interface.
    Implement this when adding the ML model in a future phase.
    """

    @abstractmethod
    async def predict(self, input_data: PhysiqueAnalysisInput) -> PhysiqueAnalysisOutput:
        """Run physique analysis and return personalised recommendations."""
        ...

    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if the model is loaded and ready to serve predictions."""
        ...


class StubPhysiquePredictor(BasePhysiquePredictor):
    """
    Stub implementation — returns deterministic output for testing.
    Replace with a real model (scikit-learn decision tree, PyTorch, etc.)
    """

    async def predict(self, input_data: PhysiqueAnalysisInput) -> PhysiqueAnalysisOutput:
        return PhysiqueAnalysisOutput(
            lagging_muscle_groups=["calves", "biceps"],
            physique_score=65.0,
            recommended_split=WorkoutSplit.PUSH_PULL_LEGS,
            recommended_days_per_week=4,
            confidence=0.0,
            model_version="stub-0.0.0",
        )

    async def is_ready(self) -> bool:
        return False  # Real model not loaded yet
