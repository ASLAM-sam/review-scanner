"""
Public API Tests
Tests customer feedback interface, QR scanning, review clicks, input validation,
slug routing, and Google Review policy compliance.
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_public_restaurant(async_client):
    response = await async_client.get("/api/v1/public/restaurant")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Paradise Test Restaurant"
    assert data["data"]["slug"] == "paradise-test-restaurant"
    assert "google_review_url" in data["data"]
    assert "primary_color" in data["data"]
    assert "secondary_color" in data["data"]


@pytest.mark.asyncio
async def test_get_public_restaurant_with_matching_slug(async_client):
    response = await async_client.get("/api/v1/public/restaurant?slug=paradise-test-restaurant")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["slug"] == "paradise-test-restaurant"


@pytest.mark.asyncio
async def test_get_public_restaurant_with_invalid_slug_returns_404(async_client):
    response = await async_client.get("/api/v1/public/restaurant?slug=non-existent-restaurant-slug")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_qr_scan_flow(async_client):
    response = await async_client.post(
        "/api/v1/public/qr/scan",
        json={"referrer": "https://camera.app"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data["data"]
    assert "destination_url" in data["data"]
    assert data["data"]["subscription_status"] == "active"


@pytest.mark.asyncio
async def test_submit_valid_feedback(async_client):
    # Scan first to obtain session
    scan_res = await async_client.post("/api/v1/public/qr/scan", json={})
    session_id = scan_res.json()["data"]["session_id"]

    feedback_payload = {
        "session_id": session_id,
        "food_rating": 5,
        "service_rating": 4,
        "ambience_rating": 5,
        "overall_experience": "positive",
        "positive_tags": ["Delicious Food", "Friendly Staff"],
        "improvement_tags": [],
        "customer_notes": "Everything was wonderful!",
    }
    response = await async_client.post("/api/v1/public/feedback", json=feedback_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["google_review_prompt_eligible"] is True


@pytest.mark.asyncio
async def test_submit_feedback_all_ratings_eligible_for_google_review(async_client):
    """
    GOOGLE POLICY COMPLIANCE:
    Every customer regardless of rating (positive, neutral, negative)
    must receive google_review_prompt_eligible = True. Zero review gating.
    """
    for rating_tuple in [(5, 5, 5, "positive"), (3, 3, 3, "neutral"), (1, 2, 1, "negative")]:
        f, s, a, overall = rating_tuple
        unique_session = f"session-compliance-{f}-{s}-{a}"

        payload = {
            "session_id": unique_session,
            "food_rating": f,
            "service_rating": s,
            "ambience_rating": a,
            "overall_experience": overall,
            "positive_tags": ["Tag"] if overall == "positive" else [],
            "improvement_tags": ["Improve"] if overall != "positive" else [],
            "customer_notes": f"Testing {overall} rating flow",
        }
        res = await async_client.post("/api/v1/public/feedback", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["google_review_prompt_eligible"] is True
        assert data["overall_experience"] == overall


@pytest.mark.asyncio
async def test_submit_feedback_without_notes_and_tags(async_client):
    payload = {
        "session_id": "session-minimal-optional-fields",
        "food_rating": 4,
        "service_rating": 4,
        "ambience_rating": 4,
        "overall_experience": "positive",
    }
    response = await async_client.post("/api/v1/public/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_submit_feedback_invalid_ratings(async_client):
    # Rating outside 1-5 range must fail validation
    invalid_payload = {
        "session_id": "test-session",
        "food_rating": 10,  # Invalid: max is 5
        "service_rating": 0,   # Invalid: min is 1
        "ambience_rating": 3,
        "overall_experience": "positive",
    }
    response = await async_client.post("/api/v1/public/feedback", json=invalid_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_feedback_invalid_overall_pattern(async_client):
    # Invalid overall experience value
    invalid_payload = {
        "session_id": "test-session-invalid-pattern",
        "food_rating": 4,
        "service_rating": 4,
        "ambience_rating": 4,
        "overall_experience": "fantastic",  # Not in (positive, neutral, negative)
    }
    response = await async_client.post("/api/v1/public/feedback", json=invalid_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_record_review_link_click(async_client):
    click_payload = {
        "session_id": "test-session-review-click",
        "target_url": "https://g.page/r/test-review",
    }
    response = await async_client.post("/api/v1/public/review-click", json=click_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["target_url"] == "https://g.page/r/test-review"


@pytest.mark.asyncio
async def test_get_qr_image_stream(async_client):
    response = await async_client.get("/api/v1/public/qr-image?format=png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 100
