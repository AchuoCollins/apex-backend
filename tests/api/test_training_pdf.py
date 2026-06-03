import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exercise import Exercise, MuscleGroup, Difficulty, Equipment, ExerciseType


@pytest.mark.asyncio
async def test_pdf_export(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    ex = Exercise(
        name="Bench Press",
        muscle_group=MuscleGroup.CHEST,
        difficulty=Difficulty.INTERMEDIATE,
        equipment=Equipment.BARBELL,
        exercise_type=ExerciseType.COMPOUND,
    )
    db_session.add(ex)
    await db_session.commit()
    await db_session.refresh(ex)

    create_r = await client.post("/api/training", headers=auth_headers, json={
        "name": "PDF Plan",
        "goal": "hypertrophy",
        "experience_level": "intermediate",
        "workout_split": "push_pull_legs",
        "exercises": [{
            "exercise_id": ex.id,
            "day_of_week": 1,
            "order_in_session": 1,
            "sets": 4,
            "reps_min": 8,
            "reps_max": 12,
            "rest_seconds": 90,
        }],
    })
    plan_id = create_r.json()["id"]

    pdf_resp = await client.get(f"/api/training/{plan_id}/pdf", headers=auth_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_pdf_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/training/99999/pdf", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_plan_with_focus_areas(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.post("/api/training/generate", headers=auth_headers, json={
        "goal": "hypertrophy",
        "experience_level": "intermediate",
        "gender": "male",
        "training_reason": "aesthetics",
        "focus_areas": ["chest"],
        "workout_split": "push_pull_legs",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["goal"] == "hypertrophy"
    assert data["workout_split"] == "push_pull_legs"
