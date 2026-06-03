"""
app/ml/prediction/prediction_service.py

Phase 7 — Prediction Service.

Single entry point for the full ML pipeline.
Orchestrates: Preprocessor → PhysiqueAnalyzer → RulesEngine →
              DecisionTreePredictor → ExerciseRecommender → TrainingGenerator

All methods return Pydantic-validated JSON-ready objects.
"""
from __future__ import annotations
import logging

from app.ml.utils.schemas import (
    PhysiqueInput, UserContext, AnalysisRequest,
    PhysiqueAnalysisResult, RuleEngineResult, DecisionTreeResult,
    RecommendationResult, TrainingPlanResult, FullAnalysisResult,
)
from app.ml.models.physique_analyzer import PhysiqueAnalyzer
from app.ml.models.rules_engine import RulesEngine
from app.ml.models.decision_tree_predictor import get_predictor
from app.ml.recommendations.exercise_recommender import ExerciseRecommender
from app.ml.recommendations.training_generator import TrainingGenerator
from app.ml.recommendations.event_planner import event_muscle_emphasis

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Orchestrates the full APEX ML pipeline.

    Usage:
        service = PredictionService()
        result  = await service.full_analysis(request)
    """

    def __init__(self) -> None:
        self._analyser    = PhysiqueAnalyzer()
        self._rules       = RulesEngine()
        self._recommender = ExerciseRecommender()
        self._generator   = TrainingGenerator()

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze_physique(self, measurements: PhysiqueInput) -> PhysiqueAnalysisResult:
        """
        Phase 1: Run physique ratio analysis.
        Returns scores, ratios, strong/weak areas, interpretation.
        """
        try:
            return self._analyser.analyse(measurements)
        except Exception as exc:
            logger.error("Physique analysis failed: %s", exc, exc_info=True)
            raise

    def evaluate_rules(
        self,
        analysis: PhysiqueAnalysisResult,
        context: UserContext,
    ) -> RuleEngineResult:
        """
        Phase 2: Fire the sports science expert rules.
        Returns coaching insights and primary training focus.
        """
        try:
            return self._rules.evaluate(analysis, context)
        except Exception as exc:
            logger.error("Rules evaluation failed: %s", exc, exc_info=True)
            raise

    def predict_weak_points(self, measurements: PhysiqueInput) -> DecisionTreeResult:
        """
        Phase 3: Run Decision Tree classifier.
        Returns muscle group focus predictions with confidence scores.
        """
        try:
            predictor = get_predictor()
            return predictor.predict(measurements)
        except FileNotFoundError:
            logger.warning("Decision tree model not found — returning stub.")
            return self._stub_dt_result()
        except Exception as exc:
            logger.error("DT prediction failed: %s", exc, exc_info=True)
            raise

    def recommend_exercises(
        self,
        weak_muscles: list[str],
        context: UserContext,
    ) -> RecommendationResult:
        """
        Phase 5: Map weak muscles to exercise prescriptions.
        Returns exercises with sets, reps, rest, frequency.
        """
        try:
            return self._recommender.recommend(weak_muscles, context)
        except Exception as exc:
            logger.error("Exercise recommendation failed: %s", exc, exc_info=True)
            raise

    def generate_training_plan(
        self,
        weak_muscles: list[str],
        context: UserContext,
    ) -> TrainingPlanResult:
        """
        Phase 6: Generate a full personalised weekly training plan.
        """
        try:
            return self._generator.generate(weak_muscles, context)
        except Exception as exc:
            logger.error("Training plan generation failed: %s", exc, exc_info=True)
            raise

    def full_analysis(self, request: AnalysisRequest) -> FullAnalysisResult:
        """
        Full pipeline — runs all phases in sequence.

        Pipeline:
          1. PhysiqueAnalyzer   → ratios, scores, strong/weak areas
          2. RulesEngine        → coaching insights
          3. DecisionTreePredictor → ML weak-point predictions (optional)
          4. ExerciseRecommender   → exercise prescriptions
          5. TrainingGenerator     → weekly plan
        """
        m = request.measurements
        ctx = request.context

        # 1. Physique analysis
        physique = self.analyze_physique(m)

        # 2. Rule engine
        rules = self.evaluate_rules(physique, ctx)

        # 3. ML prediction (graceful fallback)
        ml_result: DecisionTreeResult | None = None
        try:
            ml_result = self.predict_weak_points(m)
        except Exception:
            pass  # ML is optional — pipeline continues without it

        # 4. Determine weak muscles (combine analysis + ML + focus + event)
        weak_muscles = self._resolve_weak_muscles(physique, ml_result, rules, ctx)

        # 5. Exercise recommendations
        recommendations = self.recommend_exercises(weak_muscles, ctx)

        # 6. Training plan
        training_plan = self.generate_training_plan(weak_muscles, ctx)

        return FullAnalysisResult(
            physique_analysis=physique,
            rule_insights=rules,
            ml_prediction=ml_result,
            recommendations=recommendations,
            training_plan=training_plan,
        )

    # ── Private ───────────────────────────────────────────────────────────────

    def _resolve_weak_muscles(
        self,
        physique: PhysiqueAnalysisResult,
        ml_result: DecisionTreeResult | None,
        rules: RuleEngineResult,
        context: UserContext | None = None,
    ) -> list[str]:
        """
        Merge signals from physique analysis, ML model, rules engine, and
        the user's profile context (focus areas + event) to produce a ranked
        list of muscles to prioritise.

        Weights:
          - User-selected focus areas: 0.8 (top of list)
          - Ratio analysis lagging groups: 0.6
          - ML top predictions: 0.3 * confidence
          - Rules primary focus: 0.1
          - Event-type muscle emphasis: 0.25
        """
        scores: dict[str, float] = {}

        # Explicit user focus areas — highest weight.
        if context is not None:
            for i, m in enumerate(context.focus_areas):
                m_lower = m.lower()
                scores[m_lower] = scores.get(m_lower, 0) + (0.8 / (i + 1))

            # Event-driven muscle emphasis (only fills in, lower weight).
            for i, m in enumerate(event_muscle_emphasis(context)):
                m_lower = m.lower()
                scores[m_lower] = scores.get(m_lower, 0) + (0.25 / (i + 1))

        # Lagging from ratio analysis (high weight)
        for i, muscle in enumerate(physique.lagging_groups):
            m_lower = muscle.lower()
            scores[m_lower] = scores.get(m_lower, 0) + (0.6 / (i + 1))

        # Developing groups (moderate weight)
        for area in physique.weak_areas:
            m_lower = area.muscle.lower()
            if area.status == "developing":
                scores[m_lower] = scores.get(m_lower, 0) + 0.1

        # ML predictions
        if ml_result:
            for pred in ml_result.predictions[:3]:
                m_lower = pred.muscle_group.lower()
                scores[m_lower] = scores.get(m_lower, 0) + (0.3 * pred.confidence)

        # Rules focus
        for i, focus in enumerate(rules.primary_focus[:3]):
            m_lower = focus.lower()
            scores[m_lower] = scores.get(m_lower, 0) + (0.1 / (i + 1))

        if not scores:
            return ["shoulders", "arms", "legs"]

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [muscle for muscle, _ in ranked[:5]]

    @staticmethod
    def _stub_dt_result() -> DecisionTreeResult:
        from app.ml.utils.schemas import WeakPointPrediction
        return DecisionTreeResult(
            predictions=[
                WeakPointPrediction(muscle_group="shoulders", confidence=0.0, is_primary_focus=True)
            ],
            model_version="stub",
            top_focus="shoulders",
            feature_importance={},
        )
