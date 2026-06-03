"""
tests/ml/test_ml_personalisation.py

Tests for the personalisation upgrade:
  - Focus area prioritisation
  - Event-based plan adjustments (weeks remaining, priorities, weekly volume)
  - Gender-aware plan differences
  - Training plan output is rich enough for PDF export
"""
import pytest
import sys
import pathlib
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from app.ml.utils.schemas import (
    PhysiqueInput, UserContext, EventContext, AnalysisRequest,
)
from app.ml.recommendations.exercise_recommender import ExerciseRecommender
from app.ml.recommendations.training_generator import TrainingGenerator
from app.ml.recommendations.event_planner import (
    build_event_plan, EVENT_TYPE_PRIORITIES,
)
from app.ml.prediction.prediction_service import PredictionService


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def measurements() -> PhysiqueInput:
    return PhysiqueInput(
        height_cm=178, weight_kg=82, body_fat_pct=15,
        chest_cm=100, waist_cm=78, shoulders_cm=122,
        arms_cm=36, forearms_cm=29, neck_cm=38,
        thighs_cm=58, calves_cm=36, hips_cm=96,
        age=28, gender="male",
    )


def _future(weeks: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(weeks=weeks)


# ── Focus Area Prioritisation ────────────────────────────────────────────────

class TestFocusAreaPrioritisation:

    def test_focus_area_boosts_volume(self):
        rec = ExerciseRecommender()
        no_focus = UserContext(
            goal="hypertrophy", experience_level="intermediate",
        )
        with_focus = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            focus_areas=["chest"],
        )

        r_no   = rec.recommend(["chest"], no_focus)
        r_with = rec.recommend(["chest"], with_focus)
        assert r_with.total_weekly_sets > r_no.total_weekly_sets

    def test_focus_area_adds_priority_high(self):
        rec = ExerciseRecommender()
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            focus_areas=["shoulders"],
        )
        result = rec.recommend(["legs", "shoulders"], ctx)
        # Shoulders is a focus area → at least one recommendation marked "high"
        shoulder_recs = [r for r in result.recommendations if r.muscle_group == "shoulders"]
        assert any(r.priority == "high" for r in shoulder_recs)

    def test_focus_areas_appear_in_training_plan(self):
        gen = TrainingGenerator()
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            focus_areas=["chest", "shoulders", "core"],
        )
        plan = gen.generate(["legs"], ctx)
        # The plan exposes focus_areas
        assert "chest" in plan.focus_areas
        assert "shoulders" in plan.focus_areas

        # And exercises for at least one focus muscle appear
        muscles_trained = {e.muscle_group for s in plan.weekly_schedule for e in s.exercises}
        assert "chest" in muscles_trained or "shoulders" in muscles_trained

    def test_focus_area_changes_weak_muscle_resolution(self, measurements):
        service = PredictionService()
        ctx_no = UserContext(goal="hypertrophy", experience_level="intermediate")
        ctx_focus = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            focus_areas=["calves", "forearms"],
        )

        r_no    = service.full_analysis(AnalysisRequest(measurements=measurements, context=ctx_no))
        r_focus = service.full_analysis(AnalysisRequest(measurements=measurements, context=ctx_focus))

        muscles_focus = {r.muscle_group for r in r_focus.recommendations.recommendations}
        # User-selected focus areas should make it into the recommendation set
        assert "calves" in muscles_focus or "forearms" in muscles_focus


# ── Event-Based Recommendations ──────────────────────────────────────────────

class TestEventAwareRecommendations:

    def test_event_plan_built_for_event_context(self):
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            training_reason="event_prep",
            event=EventContext(
                event_type="bodybuilding_show",
                event_date=_future(10),
                event_name="Test Show",
            ),
        )
        ep = build_event_plan(ctx)
        assert ep is not None
        assert ep.event_type == "bodybuilding_show"
        assert ep.weeks_remaining in {9, 10}
        assert ep.training_priorities == EVENT_TYPE_PRIORITIES["bodybuilding_show"]
        assert ep.recommended_weekly_volume > 0
        assert ep.phase in {"foundation", "build", "intensification", "peak"}

    def test_event_phase_buckets(self):
        # Far event → foundation
        far = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            event=EventContext(event_type="bodybuilding_show", event_date=_future(20)),
        )
        assert build_event_plan(far).phase == "foundation"

        # Mid event → build
        mid = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            event=EventContext(event_type="bodybuilding_show", event_date=_future(8)),
        )
        assert build_event_plan(mid).phase == "build"

        # Near event → peak / taper
        near = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            event=EventContext(event_type="bodybuilding_show", event_date=_future(1)),
        )
        assert build_event_plan(near).phase == "peak"

    def test_football_event_drives_athletic_priorities(self):
        ctx = UserContext(
            goal="strength", experience_level="intermediate",
            event=EventContext(event_type="athletic_event", event_date=_future(6)),
        )
        ep = build_event_plan(ctx)
        assert ep is not None
        # Conditioning, strength, agility are the spec'd priorities
        assert ep.training_priorities == ["conditioning", "strength", "agility"]

    def test_event_drives_plan_duration_to_match_weeks_remaining(self):
        gen = TrainingGenerator()
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            event=EventContext(event_type="bodybuilding_show", event_date=_future(5)),
        )
        plan = gen.generate(["chest"], ctx)
        assert plan.duration_weeks <= 6   # Driven by weeks remaining, not default 8
        assert plan.event_plan is not None
        assert plan.event_plan.weeks_remaining in {4, 5}

    def test_plan_without_event_uses_default_duration(self):
        gen = TrainingGenerator()
        ctx = UserContext(goal="hypertrophy", experience_level="intermediate")
        plan = gen.generate(["chest"], ctx)
        assert plan.duration_weeks == 8
        assert plan.event_plan is None


# ── Gender-Aware Plans ───────────────────────────────────────────────────────

class TestGenderAwarePlans:

    def test_gender_emphasis_differs(self):
        gen = TrainingGenerator()
        female = UserContext(
            goal="hypertrophy", experience_level="intermediate", gender="female",
        )
        male = UserContext(
            goal="hypertrophy", experience_level="intermediate", gender="male",
        )
        plan_f = gen.generate(["chest"], female)
        plan_m = gen.generate(["chest"], male)

        # Implicit focus areas (no explicit user focus) should differ by gender.
        assert plan_f.focus_areas != plan_m.focus_areas

    def test_gender_notes_attached_when_gender_set(self):
        gen = TrainingGenerator()
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate", gender="female",
        )
        plan = gen.generate(["chest"], ctx)
        assert plan.gender_notes is not None
        assert "female" in plan.gender_notes.lower()

    def test_no_gender_notes_when_gender_absent(self):
        gen = TrainingGenerator()
        ctx = UserContext(goal="hypertrophy", experience_level="intermediate")
        plan = gen.generate(["chest"], ctx)
        assert plan.gender_notes is None

    def test_explicit_focus_wins_over_gender_emphasis(self):
        gen = TrainingGenerator()
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate", gender="female",
            focus_areas=["chest"],
        )
        plan = gen.generate(["legs"], ctx)
        # When explicit focus_areas are set, they take precedence
        assert plan.focus_areas == ["chest"]


# ── PDF Export Data Shape ────────────────────────────────────────────────────

class TestPDFExportData:
    """
    The PDF endpoint consumes the TrainingPlanResult. These tests assert the
    structured data needed for the PDF is present and well-formed.
    """

    def test_plan_exposes_pdf_required_fields(self):
        gen = TrainingGenerator()
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate",
            gender="male", focus_areas=["chest"],
            event=EventContext(event_type="bodybuilding_show", event_date=_future(8)),
        )
        plan = gen.generate(["chest"], ctx)

        # User-derived context
        assert plan.goal
        assert plan.focus_areas == ["chest"]
        assert plan.event_plan is not None

        # Weekly split
        assert plan.workout_split
        assert plan.days_per_week > 0
        assert len(plan.weekly_schedule) == 7

        # Exercise rows: sets/reps/rest
        first_workout = next(s for s in plan.weekly_schedule if not s.is_rest)
        for ex in first_workout.exercises:
            assert ex.sets > 0
            assert ex.reps_min > 0 and ex.reps_max >= ex.reps_min
            assert ex.rest_seconds > 0
            assert ex.muscle_group

    def test_plan_serialises_to_dict(self):
        gen = TrainingGenerator()
        ctx = UserContext(
            goal="hypertrophy", experience_level="intermediate", gender="male",
            event=EventContext(event_type="photoshoot", event_date=_future(4)),
        )
        plan = gen.generate(["chest"], ctx)
        # Pydantic model_dump should produce a fully JSON-serialisable dict
        data = plan.model_dump(mode="json")
        assert "weekly_schedule" in data
        assert "focus_areas" in data
        assert "event_plan" in data
        assert data["event_plan"]["event_type"] == "photoshoot"
