import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_empty(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/focus-areas", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_add_and_list(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/focus-areas", headers=auth_headers, json={"focus_area": "Chest"}
    )
    assert r.status_code == 201
    assert r.json()["focus_area"] == "chest"

    r2 = await client.get("/api/focus-areas", headers=auth_headers)
    assert len(r2.json()) == 1


@pytest.mark.asyncio
async def test_add_duplicate_rejected(client: AsyncClient, auth_headers: dict):
    await client.post("/api/focus-areas", headers=auth_headers, json={"focus_area": "back"})
    dup = await client.post("/api/focus-areas", headers=auth_headers, json={"focus_area": "back"})
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_bulk_replace(client: AsyncClient, auth_headers: dict):
    await client.post("/api/focus-areas", headers=auth_headers, json={"focus_area": "old"})
    resp = await client.put(
        "/api/focus-areas",
        headers=auth_headers,
        json={"focus_areas": ["glutes", "shoulders", "shoulders"]},
    )
    assert resp.status_code == 200
    names = sorted(f["focus_area"] for f in resp.json())
    assert names == ["glutes", "shoulders"]


@pytest.mark.asyncio
async def test_delete(client: AsyncClient, auth_headers: dict):
    r = await client.post("/api/focus-areas", headers=auth_headers, json={"focus_area": "legs"})
    focus_id = r.json()["id"]
    d = await client.delete(f"/api/focus-areas/{focus_id}", headers=auth_headers)
    assert d.status_code == 204
