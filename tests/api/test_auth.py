import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "first_name": "Collins",
        "last_name": "Oben",
        "email": "collins@apex.io",
        "password": "SecurePass1",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "first_name": "Collins",
        "last_name": "Oben",
        "email": "dup@apex.io",
        "password": "SecurePass1",
    }
    await client.post("/api/auth/register", json=payload)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "first_name": "Test",
        "last_name": "User",
        "email": "weak@apex.io",
        "password": "weak",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "first_name": "Login",
        "last_name": "Test",
        "email": "login@apex.io",
        "password": "SecurePass1",
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@apex.io",
        "password": "SecurePass1",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "first_name": "Wrong",
        "last_name": "Pass",
        "email": "wrongpass@apex.io",
        "password": "SecurePass1",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrongpass@apex.io",
        "password": "WrongPassword1",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={
        "first_name": "Refresh",
        "last_name": "Token",
        "email": "refresh@apex.io",
        "password": "SecurePass1",
    })
    refresh_token = reg.json()["refresh_token"]
    response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    response = await client.get("/api/users/me")
    assert response.status_code == 403
