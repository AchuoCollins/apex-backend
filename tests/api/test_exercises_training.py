import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exercise import Exercise, MuscleGroup, Difficulty, Equipment, ExerciseType
from app.models.user import User


async def create_test_exercise(db: AsyncSession, name: str = "Test Squat") -> Exercise:
    exercise = Exercise(
        name=name,
        muscle_group=MuscleGroup.LEGS,
        difficulty=Difficulty.INTERMEDIATE,
        equipment=Equipment.BARBELL,
        exercise_type=ExerciseType.COMPOUND,
        description="A test exercise.",
    )
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@pytest.mark.asyncio
async def test_get_exercises(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    await create_test_exercise(db_session, "Deadlift")
    await create_test_exercise(db_session, "Squat")

    response = await client.get("/api/exercises", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_exercise_by_id(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    ex = await create_test_exercise(db_session, "Bench Press")
    response = await client.get(f"/api/exercises/{ex.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Bench Press"


@pytest.mark.asyncio
async def test_get_exercise_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/exercises/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_filter_exercises_by_muscle(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    await create_test_exercise(db_session, "Leg Press")
    response = await client.get(
        "/api/exercises?muscle_group=legs", headers=auth_headers
    )
    assert response.status_code == 200
    for ex in response.json():
        assert ex["muscle_group"] == "legs"


# ── Training Plan Tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_training_plan(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    ex = await create_test_exercise(db_session, "Back Squat")
    response = await client.post("/api/training", headers=auth_headers, json={
        "name": "My First Plan",
        "goal": "hypertrophy",
        "experience_level": "beginner",
        "workout_split": "push_pull_legs",
        "days_per_week": 3,
        "duration_weeks": 8,
        "exercises": [
            {
                "exercise_id": ex.id,
                "day_of_week": 1,
                "order_in_session": 1,
                "sets": 4,
                "reps_min": 8,
                "reps_max": 12,
                "rest_seconds": 90,
            }
        ]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My First Plan"
    assert len(data["exercises"]) == 1


@pytest.mark.asyncio
async def test_get_training_plans(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/training", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_training_plan(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    ex = await create_test_exercise(db_session, "Overhead Press")
    create_r = await client.post("/api/training", headers=auth_headers, json={
        "name": "Plan A",
        "goal": "strength",
        "experience_level": "intermediate",
        "workout_split": "upper_lower",
        "exercises": [],
    })
    plan_id = create_r.json()["id"]

    response = await client.put(
        f"/api/training/{plan_id}", headers=auth_headers,
        json={"name": "Plan A — Updated", "days_per_week": 5}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Plan A — Updated"


@pytest.mark.asyncio
async def test_delete_training_plan(client: AsyncClient, auth_headers: dict):
    create_r = await client.post("/api/training", headers=auth_headers, json={
        "name": "Delete Me",
        "goal": "fat_loss",
        "experience_level": "beginner",
        "workout_split": "full_body",
        "exercises": [],
    })
    plan_id = create_r.json()["id"]

    del_r = await client.delete(f"/api/training/{plan_id}", headers=auth_headers)
    assert del_r.status_code == 204

    get_r = await client.get(f"/api/training/{plan_id}", headers=auth_headers)
    assert get_r.status_code == 404
