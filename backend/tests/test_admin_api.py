"""
Admin API Tests
Tests protected configuration endpoints, updates, and QR management.
"""

import pytest


@pytest.mark.asyncio
async def test_get_admin_restaurant_settings_unauthorized(async_client):
    response = await async_client.get("/api/v1/admin/restaurant")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_admin_restaurant_settings_authorized(async_client, auth_headers):
    response = await async_client.get("/api/v1/admin/restaurant", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Paradise Test Restaurant"


@pytest.mark.asyncio
async def test_update_admin_restaurant_settings(async_client, auth_headers):
    update_payload = {
        "name": "Paradise Bistro Updated",
        "primary_color": "#2563eb",
        "google_review_url": "https://g.page/r/updated-review-url",
    }
    response = await async_client.put(
        "/api/v1/admin/restaurant",
        json=update_payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Paradise Bistro Updated"
    assert data["data"]["primary_color"] == "#2563eb"
    assert data["data"]["google_review_url"] == "https://g.page/r/updated-review-url"


@pytest.mark.asyncio
async def test_get_admin_qr_details(async_client, auth_headers):
    response = await async_client.get("/api/v1/admin/qr", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "qr_svg" in data["data"]
    assert "qr_data_url" in data["data"]
    assert data["data"]["qr_data_url"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_get_admin_subscription_status(async_client, auth_headers):
    response = await async_client.get("/api/v1/admin/subscription", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "active"

