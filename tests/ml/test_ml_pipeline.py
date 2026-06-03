"""
tests/ml/test_ml_pipeline.py

Phase 10 — ML System Tests.
Tests all phases: physique analysis, rules engine, DT predictions,
exercise recommendations, and training plan generation.
"""
import pytest
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from app.ml.utils.schemas import PhysiqueInput, UserContext, AnalysisRequest
from app.ml.models.physique_analyzer import PhysiqueAnalyzer
from app.ml.models.rules_engine import RulesEngine
from app.ml.models.decision_tree_predictor import DecisionTreePredictor
from app.ml.recommendations.exercise_recommender import ExerciseRecommender
from app.ml.recommendations.training_generator import TrainingGenerator
from app.ml.prediction.prediction_service import PredictionService
from app.ml.preprocessing.preprocessor import Preprocessor


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def full_measurements() -> PhysiqueInput:
    return PhysiqueInput(
        height_cm=178, weight_kg=82, body_fat_pct=15,
        chest_cm=100, waist_cm=78, shoulders_cm=122,
        arms_cm=36, forearms_cm=29, neck_cm=38,
        thighs_cm=58, calves_cm=36, hips_cm=96,
    )


@pytest.fixture
def lagging_arms_measurements() -> PhysiqueInput:
    """Deliberately low arm circumference to trigger arm-lagging logic."""
    return PhysiqueInput(
        height_cm=178, weight_kg=82, body_fat_pct=15,
        chest_cm=100, waist_cm=78, shoulders_cm=122,
        arms_cm=28, forearms_cm=22, neck_cm=40,   # arms much smaller than neck
        thighs_cm=58, calves_cm=36, hips_cm=96,
    )


@pytest.fixture
def lagging_shoulders_measurements() -> PhysiqueInput:
    """Narrow shoulders → low shoulder-to-waist ratio."""
    return PhysiqueInput(
        height_cm=178, weight_kg=82, body_fat_pct=15,
        chest_cm=98, waist_cm=84, shoulders_cm=110,   # very narrow
        arms_cm=36, forearms_cm=29, neck_cm=38,
        thighs_cm=58, calves_cm=36, hips_cm=96,
    )


@pytest.fixture
def minimal_measurements() -> PhysiqueInput:
    """Only essential fields filled — tests graceful handling of missing data."""
    return PhysiqueInput(
        height_cm=175, weight_kg=75,
        shoulders_cm=115, waist_cm=80,
    )


@pytest.fixture
def hypertrophy_intermediate() -> UserContext:
    return UserContext(goal="hypertrophy", experience_level="intermediate")


@pytest.fixture
def strength_beginner() -> UserContext:
    return UserContext(goal="strength", experience_level="beginner")


@pytest.fixture
def fat_loss_advanced() -> UserContext:
    return UserContext(goal="fat_loss", experience_level="advanced")


# ── Preprocessor Tests ────────────────────────────────────────────────────────

class TestPreprocessor:

    def test_computes_ratios_from_full_data(self, full_measurements):
        p = Preprocessor()
        features = p.process(full_measurements)
        assert features.ratios.get("shoulder_to_waist") is not None
        assert features.ratios.get("arm_to_neck") is not None
        assert features.completeness_pct > 80

    def test_handles_missing_fields_gracefully(self, minimal_measurements):
        p = Preprocessor()
        features = p.process(minimal_measurements)
        assert features.ratios.get("shoulder_to_waist") is not None
        assert features.ratios.get("arm_to_neck") is None  # neck not provided
        assert features.completeness_pct < 50

    def test_feature_vector_shape(self, full_measurements):
        p = Preprocessor()
        features = p.process(full_measurements)
        assert len(features.feature_vector) > 10
        assert len(features.feature_names) == len(features.feature_vector)

    def test_composites_computed(self, full_measurements):
        p = Preprocessor()
        features = p.process(full_measurements)
        assert features.composites.get("bmi") is not None
        assert features.composites.get("ffmi") is not None
        assert 15 < features.composites["bmi"] < 40


# ── Physique Analyzer Tests ───────────────────────────────────────────────────

class TestPhysiqueAnalyzer:

    def test_returns_analysis_result(self, full_measurements):
        analyzer = PhysiqueAnalyzer()
        result = analyzer.analyse(full_measurements)
        assert 0 <= result.physique_score <= 100
        assert 0 <= result.symmetry_score <= 100
        assert result.grade in {"A+", "A", "B", "C", "D", "F"}
        assert result.label in {"Elite", "Advanced", "Developing", "Foundation", "Beginner"}

    def test_detects_lagging_arms(self, lagging_arms_measurements):
        analyzer = PhysiqueAnalyzer()
        result = analyzer.analyse(lagging_arms_measurements)
        lagging_muscles = [r.primary_muscle for r in result.ratios if r.status == "lagging"]
        assert "Arms" in lagging_muscles or len(result.weak_areas) > 0

    def test_detects_lagging_shoulders(self, lagging_shoulders_measurements):
        analyzer = PhysiqueAnalyzer()
        result = analyzer.analyse(lagging_shoulders_measurements)
        lagging = [r.primary_muscle for r in result.ratios if r.status in ("lagging", "developing")]
        assert "Shoulders" in lagging

    def test_handles_minimal_data(self, minimal_measurements):
        analyzer = PhysiqueAnalyzer()
        result = analyzer.analyse(minimal_measurements)
        assert result.physique_score >= 0
        assert result.data_completeness < 50
        assert len(result.ratios) >= 1   # At least shoulder-to-waist computed

    def test_score_lower_for_lagging_physique(
        self, full_measurements, lagging_shoulders_measurements
    ):
        analyzer = PhysiqueAnalyzer()
        good   = analyzer.analyse(full_measurements)
        lagging = analyzer.analyse(lagging_shoulders_measurements)
        assert lagging.physique_score < good.physique_score

    def test_strong_areas_populated(self, full_measurements):
        analyzer = PhysiqueAnalyzer()
        result = analyzer.analyse(full_measurements)
        # Should have some ratios evaluated
        assert len(result.ratios) >= 3

    def test_interpretation_is_string(self, full_measurements):
        analyzer = PhysiqueAnalyzer()
        result = analyzer.analyse(full_measurements)
        assert isinstance(result.interpretation, str)
        assert len(result.interpretation) > 20

    def test_bmi_ffmi_computed(self, full_measurements):
        analyzer = PhysiqueAnalyzer()
        result = analyzer.analyse(full_measurements)
        assert result.bmi is not None
        assert result.ffmi is not None
        assert 15 < result.bmi < 40
        assert 15 < result.ffmi < 35


# ── Rules Engine Tests ────────────────────────────────────────────────────────

class TestRulesEngine:

    def test_fires_shoulder_rule(self, lagging_shoulders_measurements, hypertrophy_intermediate):
        analyzer = PhysiqueAnalyzer()
        analysis = analyzer.analyse(lagging_shoulders_measurements)
        engine   = RulesEngine()
        result   = engine.evaluate(analysis, hypertrophy_intermediate)
        rule_ids = [i.rule_id for i in result.insights]
        assert "PROP_001" in rule_ids    # Shoulder Width Deficit rule

    def test_fires_arm_rule(self, lagging_arms_measurements, hypertrophy_intermediate):
        analyzer = PhysiqueAnalyzer()
        analysis = analyzer.analyse(lagging_arms_measurements)
        engine   = RulesEngine()
        result   = engine.evaluate(analysis, hypertrophy_intermediate)
        rule_ids = [i.rule_id for i in result.insights]
        assert "PROP_002" in rule_ids    # Arm Development Lagging rule

    def test_goal_specific_rule_fires(self, full_measurements, hypertrophy_intermediate):
        analyzer = PhysiqueAnalyzer()
        analysis = analyzer.analyse(full_measurements)
        engine   = RulesEngine()
        result   = engine.evaluate(analysis, hypertrophy_intermediate)
        goal_rules = [i for i in result.insights if i.category == "goal"]
        assert len(goal_rules) >= 1

    def test_insights_have_required_fields(self, full_measurements, hypertrophy_intermediate):
        analyzer = PhysiqueAnalyzer()
        analysis = analyzer.analyse(full_measurements)
        engine   = RulesEngine()
        result   = engine.evaluate(analysis, hypertrophy_intermediate)
        for insight in result.insights:
            assert insight.rule_id
            assert insight.title
            assert insight.explanation
            assert insight.action
            assert insight.priority in {"high", "medium", "low"}

    def test_primary_focus_populated(self, lagging_arms_measurements, hypertrophy_intermediate):
        analyzer = PhysiqueAnalyzer()
        analysis = analyzer.analyse(lagging_arms_measurements)
        engine   = RulesEngine()
        result   = engine.evaluate(analysis, hypertrophy_intermediate)
        assert isinstance(result.primary_focus, list)


# ── Decision Tree Tests ───────────────────────────────────────────────────────

class TestDecisionTree:

    def test_loads_and_predicts(self, full_measurements):
        predictor = DecisionTreePredictor()
        predictor.load()
        assert predictor.is_ready()
        result = predictor.predict(full_measurements)
        assert result.model_version == "1.0.0"
        assert len(result.predictions) == 7   # one per class
        assert result.top_focus in {
            "arms", "calves", "chest", "forearms", "glutes", "legs", "shoulders"
        }

    def test_confidence_sum_approx_one(self, full_measurements):
        predictor = DecisionTreePredictor()
        predictor.load()
        result = predictor.predict(full_measurements)
        total = sum(p.confidence for p in result.predictions)
        assert abs(total - 1.0) < 0.01   # Probabilities sum to ~1

    def test_primary_focus_is_highest_confidence(self, full_measurements):
        predictor = DecisionTreePredictor()
        predictor.load()
        result = predictor.predict(full_measurements)
        primary = [p for p in result.predictions if p.is_primary_focus]
        assert len(primary) == 1
        top_conf = max(p.confidence for p in result.predictions)
        assert primary[0].confidence == top_conf

    def test_predicts_arms_for_lagging_arms(self, lagging_arms_measurements):
        predictor = DecisionTreePredictor()
        predictor.load()
        result = predictor.predict(lagging_arms_measurements)
        # Top prediction should strongly favour arms
        top_preds = sorted(result.predictions, key=lambda p: p.confidence, reverse=True)
        top3 = [p.muscle_group for p in top_preds[:3]]
        assert "arms" in top3 or "forearms" in top3

    def test_feature_importance_populated(self, full_measurements):
        predictor = DecisionTreePredictor()
        predictor.load()
        result = predictor.predict(full_measurements)
        assert len(result.feature_importance) > 0


# ── Exercise Recommender Tests ────────────────────────────────────────────────

class TestExerciseRecommender:

    def test_returns_recommendations(self, hypertrophy_intermediate):
        rec = ExerciseRecommender()
        result = rec.recommend(["arms", "calves"], hypertrophy_intermediate)
        assert len(result.recommendations) > 0
        assert result.total_weekly_sets > 0
        assert result.estimated_sessions > 0

    def test_recommendation_fields_complete(self, hypertrophy_intermediate):
        rec = ExerciseRecommender()
        result = rec.recommend(["shoulders"], hypertrophy_intermediate)
        for r in result.recommendations:
            assert r.name
            assert r.sets > 0
            assert r.reps_min > 0
            assert r.reps_max >= r.reps_min
            assert r.rest_seconds > 0
            assert r.exercise_type in {"compound", "isolation"}

    def test_respects_goal_prescription(self):
        rec = ExerciseRecommender()
        ctx_strength = UserContext(goal="strength", experience_level="intermediate")
        ctx_hyper    = UserContext(goal="hypertrophy", experience_level="intermediate")
        r_s = rec.recommend(["chest"], ctx_strength)
        r_h = rec.recommend(["chest"], ctx_hyper)
        # Strength should have lower reps
        s_reps = min(r.reps_max for r in r_s.recommendations if r.exercise_type == "compound")
        h_reps = min(r.reps_max for r in r_h.recommendations if r.exercise_type == "compound")
        assert s_reps <= h_reps

    def test_max_five_muscle_groups(self, hypertrophy_intermediate):
        rec = ExerciseRecommender()
        result = rec.recommend(
            ["arms", "calves", "chest", "shoulders", "legs", "back", "core"],
            hypertrophy_intermediate
        )
        muscles_in_result = {r.muscle_group for r in result.recommendations}
        assert len(muscles_in_result) <= 6   # capped at 5 groups, some have 2 muscles


# ── Training Generator Tests ──────────────────────────────────────────────────

class TestTrainingGenerator:

    def test_generates_full_week(self, hypertrophy_intermediate):
        gen = TrainingGenerator()
        plan = gen.generate(["arms", "calves"], hypertrophy_intermediate)
        assert len(plan.weekly_schedule) == 7   # Mon–Sun always populated
        assert plan.total_weekly_sets > 0
        assert plan.days_per_week >= 3

    def test_rest_days_have_no_exercises(self, hypertrophy_intermediate):
        gen = TrainingGenerator()
        plan = gen.generate(["shoulders"], hypertrophy_intermediate)
        for session in plan.weekly_schedule:
            if session.is_rest:
                assert len(session.exercises) == 0
                assert session.total_sets == 0

    def test_plan_name_contains_goal(self, hypertrophy_intermediate):
        gen = TrainingGenerator()
        plan = gen.generate(["arms"], hypertrophy_intermediate)
        assert "hypertrophy" in plan.plan_name.lower() or "push" in plan.plan_name.lower()

    def test_progression_notes_present(self, hypertrophy_intermediate):
        gen = TrainingGenerator()
        plan = gen.generate(["legs"], hypertrophy_intermediate)
        assert len(plan.progression_notes) > 10
        assert len(plan.volume_notes) > 10

    def test_beginner_gets_full_body(self):
        ctx = UserContext(goal="hypertrophy", experience_level="beginner")
        gen = TrainingGenerator()
        plan = gen.generate(["shoulders"], ctx)
        assert "full_body" in plan.workout_split or plan.days_per_week <= 4

    def test_advanced_gets_more_volume(self):
        ctx_beg = UserContext(goal="hypertrophy", experience_level="beginner")
        ctx_adv = UserContext(goal="hypertrophy", experience_level="advanced")
        gen = TrainingGenerator()
        p_beg = gen.generate(["arms"], ctx_beg)
        p_adv = gen.generate(["arms"], ctx_adv)
        assert p_adv.total_weekly_sets >= p_beg.total_weekly_sets


# ── Full Pipeline Tests ───────────────────────────────────────────────────────

class TestFullPipeline:

    def test_full_analysis_returns_all_components(
        self, full_measurements, hypertrophy_intermediate
    ):
        service = PredictionService()
        request = AnalysisRequest(
            measurements=full_measurements,
            context=hypertrophy_intermediate,
        )
        result = service.full_analysis(request)
        assert result.physique_analysis is not None
        assert result.rule_insights is not None
        assert result.recommendations is not None
        assert result.training_plan is not None

    def test_full_analysis_with_minimal_data(self):
        service = PredictionService()
        request = AnalysisRequest(
            measurements=PhysiqueInput(
                height_cm=175, weight_kg=75,
                shoulders_cm=115, waist_cm=80,
            ),
            context=UserContext(goal="hypertrophy", experience_level="beginner"),
        )
        result = service.full_analysis(request)
        assert result.physique_analysis.physique_score >= 0
        assert len(result.training_plan.weekly_schedule) == 7

    def test_weak_muscle_resolution(self, lagging_arms_measurements, hypertrophy_intermediate):
        service = PredictionService()
        request = AnalysisRequest(
            measurements=lagging_arms_measurements,
            context=hypertrophy_intermediate,
        )
        result = service.full_analysis(request)
        # Arms should appear in recommendations
        muscles = {r.muscle_group for r in result.recommendations.recommendations}
        assert "biceps" in muscles or "triceps" in muscles or "arms" in muscles

    def test_pipeline_consistent_across_calls(
        self, full_measurements, hypertrophy_intermediate
    ):
        service = PredictionService()
        request = AnalysisRequest(
            measurements=full_measurements,
            context=hypertrophy_intermediate,
        )
        r1 = service.full_analysis(request)
        r2 = service.full_analysis(request)
        assert r1.physique_analysis.physique_score == r2.physique_analysis.physique_score
        assert r1.physique_analysis.lagging_groups == r2.physique_analysis.lagging_groups
