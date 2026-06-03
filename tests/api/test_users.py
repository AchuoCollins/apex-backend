import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@apex.io"
    assert data["first_name"] == "Test"


@pytest.mark.asyncio
async def test_update_me_name(client: AsyncClient, auth_headers: dict):
    response = await client.put("/api/users/me", headers=auth_headers, json={
        "first_name": "Updated",
        "last_name": "Name",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"


@pytest.mark.asyncio
async def test_update_me_profile(client: AsyncClient, auth_headers: dict):
    response = await client.put("/api/users/me", headers=auth_headers, json={
        "profile": {
            "age": 25,
            "gender": "male",
            "height_cm": 178.0,
            "weight_kg": 82.0,
            "fitness_goal": "hypertrophy",
            "experience_level": "intermediate",
            "training_reason": "aesthetics",
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["age"] == 25
    assert data["profile"]["gender"] == "male"
    assert data["profile"]["fitness_goal"] == "hypertrophy"
    assert data["profile"]["training_reason"] == "aesthetics"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/users/me")
    assert response.status_code == 403
