"""initial schema — full APEX baseline

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-02

Establishes the full baseline schema for the APEX backend, including
all existing tables and the new focus areas / events tables and the
training_reason profile column.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


# ── Enum names ────────────────────────────────────────────────────────────────
FITNESS_GOAL    = sa.Enum("hypertrophy", "strength", "fat_loss", "body_recomposition", name="fitnessgoal")
EXPERIENCE      = sa.Enum("beginner", "intermediate", "advanced", name="experiencelevel")
GENDER          = sa.Enum("male", "female", "other", name="gender")
TRAINING_REASON = sa.Enum(
    "general_fitness", "competition", "event_prep", "health",
    "aesthetics", "performance", "rehabilitation",
    name="trainingreason",
)
MUSCLE_GROUP    = sa.Enum("chest", "back", "shoulders", "biceps", "triceps", "legs", "calves", "core", name="musclegroup")
DIFFICULTY      = sa.Enum("beginner", "intermediate", "advanced", name="difficulty")
EQUIPMENT       = sa.Enum("barbell", "dumbbell", "cable", "machine", "bodyweight", "kettlebell", "band", "other", name="equipment")
EXERCISE_TYPE   = sa.Enum("compound", "isolation", name="exercisetype")
WORKOUT_SPLIT   = sa.Enum("push_pull_legs", "upper_lower", "bro_split", "full_body", name="workoutsplit")
EVENT_TYPE      = sa.Enum(
    "bodybuilding_show", "powerlifting_meet", "photoshoot", "wedding",
    "vacation", "athletic_event", "other",
    name="eventtype",
)


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name",  sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active",    sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])

    # ── user_profiles ────────────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", GENDER, nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("fitness_goal", FITNESS_GOAL, nullable=True),
        sa.Column("experience_level", EXPERIENCE, nullable=True),
        sa.Column("training_reason", TRAINING_REASON, nullable=True),
        sa.Column("bio", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])

    # ── body_metrics ─────────────────────────────────────────────────────────
    op.create_table(
        "body_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("body_fat_pct", sa.Float(), nullable=True),
        sa.Column("chest_cm", sa.Float(), nullable=True),
        sa.Column("waist_cm", sa.Float(), nullable=True),
        sa.Column("shoulders_cm", sa.Float(), nullable=True),
        sa.Column("arms_cm", sa.Float(), nullable=True),
        sa.Column("forearms_cm", sa.Float(), nullable=True),
        sa.Column("neck_cm", sa.Float(), nullable=True),
        sa.Column("thighs_cm", sa.Float(), nullable=True),
        sa.Column("calves_cm", sa.Float(), nullable=True),
        sa.Column("hips_cm", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_body_metrics_user_id", "body_metrics", ["user_id"])
    op.create_index("ix_body_metrics_user_created", "body_metrics", ["user_id", "created_at"])

    # ── exercises ────────────────────────────────────────────────────────────
    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("muscle_group", MUSCLE_GROUP, nullable=False),
        sa.Column("difficulty", DIFFICULTY, nullable=False),
        sa.Column("equipment", EQUIPMENT, nullable=False),
        sa.Column("exercise_type", EXERCISE_TYPE, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_exercises_name", "exercises", ["name"])
    op.create_index("ix_exercises_muscle_group", "exercises", ["muscle_group"])
    op.create_index("ix_exercises_muscle_difficulty", "exercises", ["muscle_group", "difficulty"])

    # ── training_plans ───────────────────────────────────────────────────────
    op.create_table(
        "training_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal", FITNESS_GOAL, nullable=False),
        sa.Column("experience_level", EXPERIENCE, nullable=False),
        sa.Column("workout_split", WORKOUT_SPLIT, nullable=False),
        sa.Column("days_per_week", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("duration_weeks", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ai_model_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_training_plans_user_id", "training_plans", ["user_id"])
    op.create_index("ix_training_plans_user_active", "training_plans", ["user_id", "is_active"])

    # ── training_plan_exercises ──────────────────────────────────────────────
    op.create_table(
        "training_plan_exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("order_in_session", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps_min", sa.Integer(), nullable=False),
        sa.Column("reps_max", sa.Integer(), nullable=False),
        sa.Column("rest_seconds", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_training_plan_exercises_plan_id", "training_plan_exercises", ["plan_id"])
    op.create_index("ix_tpe_plan_day", "training_plan_exercises", ["plan_id", "day_of_week"])

    # ── refresh_tokens ───────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(500), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"])
    op.create_index("ix_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "is_revoked"])

    # ── user_focus_areas ─────────────────────────────────────────────────────
    op.create_table(
        "user_focus_areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("focus_area", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "focus_area", name="uq_user_focus_area"),
    )
    op.create_index("ix_user_focus_areas_user_id", "user_focus_areas", ["user_id"])
    op.create_index("ix_user_focus_areas_user", "user_focus_areas", ["user_id"])

    # ── events ───────────────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_name", sa.String(200), nullable=False),
        sa.Column("event_type", EVENT_TYPE, nullable=False),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_events_user_id", "events", ["user_id"])
    op.create_index("ix_events_user_date", "events", ["user_id", "event_date"])


def downgrade() -> None:
    op.drop_index("ix_events_user_date", table_name="events")
    op.drop_index("ix_events_user_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_user_focus_areas_user", table_name="user_focus_areas")
    op.drop_index("ix_user_focus_areas_user_id", table_name="user_focus_areas")
    op.drop_table("user_focus_areas")

    op.drop_index("ix_refresh_tokens_user_revoked", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_tpe_plan_day", table_name="training_plan_exercises")
    op.drop_index("ix_training_plan_exercises_plan_id", table_name="training_plan_exercises")
    op.drop_table("training_plan_exercises")

    op.drop_index("ix_training_plans_user_active", table_name="training_plans")
    op.drop_index("ix_training_plans_user_id", table_name="training_plans")
    op.drop_table("training_plans")

    op.drop_index("ix_exercises_muscle_difficulty", table_name="exercises")
    op.drop_index("ix_exercises_muscle_group", table_name="exercises")
    op.drop_index("ix_exercises_name", table_name="exercises")
    op.drop_table("exercises")

    op.drop_index("ix_body_metrics_user_created", table_name="body_metrics")
    op.drop_index("ix_body_metrics_user_id", table_name="body_metrics")
    op.drop_table("body_metrics")

    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")

    op.drop_index("ix_users_email_active", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    # Drop enums (PostgreSQL)
    bind = op.get_bind()
    for enum_obj in (
        EVENT_TYPE, WORKOUT_SPLIT, EXERCISE_TYPE, EQUIPMENT, DIFFICULTY,
        MUSCLE_GROUP, TRAINING_REASON, GENDER, EXPERIENCE, FITNESS_GOAL,
    ):
        enum_obj.drop(bind, checkfirst=True)
