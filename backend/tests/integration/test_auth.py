import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "test@allocensus.com",
        "password": "TestPass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "wallet_address" in data
    assert data["wallet_address"].startswith("0x")


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"email": "dup@allocensus.com", "password": "TestPass123", "full_name": "Dup"}
    await client.post("/api/auth/register", json=payload)
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@allocensus.com", "password": "TestPass123", "full_name": "Login User"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@allocensus.com", "password": "TestPass123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={
        "email": "login@allocensus.com", "password": "WrongPass999"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
