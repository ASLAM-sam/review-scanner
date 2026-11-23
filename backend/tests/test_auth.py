"""
Authentication and Authorization Tests
Verifies password hashing, token encoding/decoding, login flow, and endpoint guards.
"""

import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    raw_password = "SuperSecretPassword123"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_lifecycle():
    data = {"sub": "admin@restaurant.com", "custom_claim": "test"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "admin@restaurant.com"
    assert decoded["custom_claim"] == "test"
    assert "exp" in decoded


def test_jwt_invalid_token():
    assert decode_access_token("invalid.token.signature") is None


@pytest.mark.asyncio
async def test_admin_login_success(async_client):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@restaurant.com", "password": "TestPassword123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_admin_login_failure(async_client):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@restaurant.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_me_endpoint_authorized(async_client, auth_headers):
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["email"] == "testadmin@restaurant.com"


@pytest.mark.asyncio
async def test_protected_me_endpoint_unauthorized(async_client):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401
