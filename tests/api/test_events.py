import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient


def _future(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


@pytest.mark.asyncio
async def test_create_and_list_event(client: AsyncClient, auth_headers: dict):
    payload = {
        "event_name": "Summer Show",
        "event_type": "bodybuilding_show",
        "event_date": _future(60),
    }
    r = await client.post("/api/events", headers=auth_headers, json=payload)
    assert r.status_code == 201
    assert r.json()["event_name"] == "Summer Show"

    r2 = await client.get("/api/events", headers=auth_headers)
    assert r2.status_code == 200
    assert len(r2.json()) == 1


@pytest.mark.asyncio
async def test_update_event(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/events", headers=auth_headers,
        json={"event_name": "Photo", "event_type": "photoshoot", "event_date": _future(15)},
    )
    event_id = r.json()["id"]

    upd = await client.put(
        f"/api/events/{event_id}", headers=auth_headers,
        json={"event_name": "Photoshoot — Studio"},
    )
    assert upd.status_code == 200
    assert upd.json()["event_name"] == "Photoshoot — Studio"


@pytest.mark.asyncio
async def test_delete_event(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/events", headers=auth_headers,
        json={"event_name": "Wedding", "event_type": "wedding", "event_date": _future(120)},
    )
    eid = r.json()["id"]
    d = await client.delete(f"/api/events/{eid}", headers=auth_headers)
    assert d.status_code == 204
    g = await client.get(f"/api/events/{eid}", headers=auth_headers)
    assert g.status_code == 404


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/events/99999", headers=auth_headers)
    assert r.status_code == 404
