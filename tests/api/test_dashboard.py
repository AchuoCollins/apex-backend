import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["focus_areas"] == []
    assert data["event"] is None
    assert data["current_training_plan"] is None


@pytest.mark.asyncio
async def test_dashboard_populated(client: AsyncClient, auth_headers: dict):
    # Profile goal
    await client.put("/api/users/me", headers=auth_headers, json={
        "profile": {"fitness_goal": "hypertrophy", "experience_level": "intermediate"}
    })
    # Focus areas
    await client.put("/api/focus-areas", headers=auth_headers, json={
        "focus_areas": ["chest", "arms"],
    })
    # Event
    future = (datetime.now(timezone.utc) + timedelta(days=42)).isoformat()
    await client.post("/api/events", headers=auth_headers, json={
        "event_name": "Show", "event_type": "bodybuilding_show", "event_date": future,
    })
    # Plan
    await client.post("/api/training", headers=auth_headers, json={
        "name": "My Plan",
        "goal": "hypertrophy",
        "experience_level": "intermediate",
        "workout_split": "push_pull_legs",
        "exercises": [],
    })

    resp = await client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["goal"] == "hypertrophy"
    assert set(data["focus_areas"]) == {"chest", "arms"}
    assert data["event"]["event_name"] == "Show"
    assert data["event"]["days_remaining"] >= 40
    assert data["current_training_plan"]["name"] == "My Plan"
