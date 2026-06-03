import pytest
from httpx import AsyncClient

SAMPLE_METRICS = {
    "height_cm": 178.0,
    "weight_kg": 82.0,
    "chest_cm": 100.0,
    "waist_cm": 78.0,
    "shoulders_cm": 122.0,
    "arms_cm": 38.0,
    "neck_cm": 38.0,
    "thighs_cm": 58.0,
    "calves_cm": 36.0,
    "hips_cm": 96.0,
}


@pytest.mark.asyncio
async def test_create_metrics(client: AsyncClient, auth_headers: dict):
    response = await client.post("/api/metrics", headers=auth_headers, json=SAMPLE_METRICS)
    assert response.status_code == 201
    data = response.json()
    assert data["waist_cm"] == 78.0
    assert data["shoulders_cm"] == 122.0
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_metrics_list(client: AsyncClient, auth_headers: dict):
    # Create 2 entries
    await client.post("/api/metrics", headers=auth_headers, json=SAMPLE_METRICS)
    await client.post("/api/metrics", headers=auth_headers, json={**SAMPLE_METRICS, "weight_kg": 83.0})

    response = await client.get("/api/metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_metrics_by_id(client: AsyncClient, auth_headers: dict):
    create_r = await client.post("/api/metrics", headers=auth_headers, json=SAMPLE_METRICS)
    metrics_id = create_r.json()["id"]

    response = await client.get(f"/api/metrics/{metrics_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == metrics_id


@pytest.mark.asyncio
async def test_update_metrics(client: AsyncClient, auth_headers: dict):
    create_r = await client.post("/api/metrics", headers=auth_headers, json=SAMPLE_METRICS)
    metrics_id = create_r.json()["id"]

    response = await client.put(
        f"/api/metrics/{metrics_id}", headers=auth_headers,
        json={"weight_kg": 84.5, "waist_cm": 77.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["weight_kg"] == 84.5
    assert data["waist_cm"] == 77.0


@pytest.mark.asyncio
async def test_delete_metrics(client: AsyncClient, auth_headers: dict):
    create_r = await client.post("/api/metrics", headers=auth_headers, json=SAMPLE_METRICS)
    metrics_id = create_r.json()["id"]

    del_r = await client.delete(f"/api/metrics/{metrics_id}", headers=auth_headers)
    assert del_r.status_code == 204

    get_r = await client.get(f"/api/metrics/{metrics_id}", headers=auth_headers)
    assert get_r.status_code == 404


@pytest.mark.asyncio
async def test_get_metrics_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/metrics/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_latest_metrics(client: AsyncClient, auth_headers: dict):
    await client.post("/api/metrics", headers=auth_headers, json=SAMPLE_METRICS)
    await client.post("/api/metrics", headers=auth_headers, json={**SAMPLE_METRICS, "weight_kg": 85.0})

    response = await client.get("/api/metrics/latest", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["weight_kg"] == 85.0
