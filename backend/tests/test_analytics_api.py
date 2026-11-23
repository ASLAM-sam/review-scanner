"""
Analytics API Tests
Verifies that only the 4 required categories are computed and presented accurately.
1. Total QR scans
2. Total feedback submissions
3. Google review link clicks
4. Monthly activity
"""

import pytest


@pytest.mark.asyncio
async def test_analytics_overview_unauthorized(async_client):
    response = await async_client.get("/api/v1/analytics/overview")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analytics_overview_authorized_and_accurate_counts(async_client, auth_headers):
    # 1. Check initial counts
    res_initial = await async_client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert res_initial.status_code == 200
    data_initial = res_initial.json()["data"]

    initial_scans = data_initial["total_qr_scans"]
    initial_feedbacks = data_initial["total_feedback_submissions"]
    initial_clicks = data_initial["google_review_link_clicks"]
    assert "monthly_activity" in data_initial

    # 2. Trigger a QR scan
    scan_res = await async_client.post("/api/v1/public/qr/scan", json={})
    assert scan_res.status_code == 200
    session_id = scan_res.json()["data"]["session_id"]

    # 3. Trigger feedback submission
    fb_res = await async_client.post(
        "/api/v1/public/feedback",
        json={
            "session_id": session_id,
            "food_rating": 5,
            "service_rating": 5,
            "ambience_rating": 5,
            "overall_experience": "positive",
        },
    )
    assert fb_res.status_code == 200

    # 4. Trigger review click
    click_res = await async_client.post(
        "/api/v1/public/review-click",
        json={"session_id": session_id},
    )
    assert click_res.status_code == 200

    # 5. Fetch updated analytics and verify increments
    res_updated = await async_client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert res_updated.status_code == 200
    data_updated = res_updated.json()["data"]

    assert data_updated["total_qr_scans"] == initial_scans + 1
    assert data_updated["total_feedback_submissions"] == initial_feedbacks + 1
    assert data_updated["google_review_link_clicks"] == initial_clicks + 1
    assert len(data_updated["monthly_activity"]) >= 1

