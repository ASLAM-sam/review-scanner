"""
Analytics Dashboard Automated Tests
Verifies:
- Authentication & authorization gates (unauthenticated, invalid, expired, inactive)
- Accurate summary counts (QR scans, feedback submissions, Google review clicks)
- 12-month chronological timeline including zero-activity months
- Timezone-aware date boundary calculations
- Absolute customer privacy (no customer notes, prompts, PII, or IPs exposed)
"""

from datetime import datetime, timedelta, timezone
import zoneinfo
import pytest
import jwt

from app.core.config import settings
from app.db.collections import (
    COLLECTION_FEEDBACK_SUBMISSIONS,
    COLLECTION_QR_SCANS,
    COLLECTION_REVIEW_LINK_CLICKS,
)


@pytest.mark.asyncio
async def test_dashboard_analytics_unauthorized(async_client):
    response = await async_client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_analytics_invalid_token(async_client):
    response = await async_client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_analytics_expired_token(async_client):
    expired_payload = {
        "sub": "admin@restaurant.com",
        "exp": datetime.now(timezone.utc) - timedelta(hours=2),
        "iat": datetime.now(timezone.utc) - timedelta(hours=3),
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    response = await async_client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_analytics_inactive_admin(async_client, mock_db):
    # Set admin to inactive
    await mock_db.admin_users.update_one(
        {"email": "admin@restaurant.com"},
        {"$set": {"is_active": False}},
    )
    try:
        # Generate valid token for inactive admin
        valid_payload = {
            "sub": "admin@restaurant.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(valid_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        response = await async_client.get(
            "/api/v1/analytics/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
    finally:
        # Restore active state
        await mock_db.admin_users.update_one(
            {"email": "admin@restaurant.com"},
            {"$set": {"is_active": True}},
        )


@pytest.mark.asyncio
async def test_dashboard_analytics_empty_database_returns_zeroes(async_client, admin_token, mock_db):
    # Clean data collections
    await mock_db[COLLECTION_QR_SCANS].delete_many({})
    await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].delete_many({})
    await mock_db[COLLECTION_REVIEW_LINK_CLICKS].delete_many({})

    response = await async_client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # Summary must be all zeroes
    assert data["summary"]["total_scans"] == 0
    assert data["summary"]["total_feedback_submissions"] == 0
    assert data["summary"]["total_review_link_clicks"] == 0
    assert data["summary"]["raw_scans"] == 0

    # Monthly activity must have exactly 12 months with 0 counts
    months = data["monthly_activity"]["months"]
    assert len(months) == 12
    for m in months:
        assert m["scans"] == 0
        assert m["feedbacks"] == 0
        assert m["review_clicks"] == 0


@pytest.mark.asyncio
async def test_dashboard_analytics_counts_and_bot_filtering(async_client, admin_token, mock_db):
    # Clean collections
    await mock_db[COLLECTION_QR_SCANS].delete_many({})
    await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].delete_many({})
    await mock_db[COLLECTION_REVIEW_LINK_CLICKS].delete_many({})

    now = datetime.now(timezone.utc)

    # Insert 3 human unique scans + 1 bot scan + 1 non-unique refresh
    await mock_db[COLLECTION_QR_SCANS].insert_many([
        {"session_id": "s1", "created_at": now, "is_unique": True, "is_bot": False},
        {"session_id": "s2", "created_at": now, "is_unique": True, "is_bot": False},
        {"session_id": "s3", "created_at": now, "is_unique": True, "is_bot": False},
        {"session_id": "s4", "created_at": now, "is_unique": True, "is_bot": True},  # Bot: excluded from total
        {"session_id": "s1", "created_at": now, "is_unique": False, "is_bot": False}, # Reload: non-unique
    ])

    # Insert 2 feedback submissions
    await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].insert_many([
        {
            "session_id": "s1",
            "food_rating": 5,
            "service_rating": 5,
            "ambience_rating": 5,
            "overall_experience": "positive",
            "customer_notes": "Superb taste!",
            "created_at": now,
        },
        {
            "session_id": "s2",
            "food_rating": 4,
            "service_rating": 4,
            "ambience_rating": 4,
            "overall_experience": "positive",
            "customer_notes": "Very nice",
            "created_at": now,
        },
    ])

    # Insert 1 Google review link click
    await mock_db[COLLECTION_REVIEW_LINK_CLICKS].insert_one({
        "session_id": "s1",
        "target_url": "https://g.page/r/test",
        "created_at": now,
    })

    response = await async_client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # Verify Metric 1: Total QR Scans = 3 (human unique, excluding bot and reload)
    assert data["summary"]["total_scans"] == 3
    # Raw scans = 5
    assert data["summary"]["raw_scans"] == 5

    # Verify Metric 2: Feedback Submissions = 2
    assert data["summary"]["total_feedback_submissions"] == 2

    # Verify Metric 3: Google Review Clicks = 1
    assert data["summary"]["total_review_link_clicks"] == 1


@pytest.mark.asyncio
async def test_dashboard_analytics_12_months_chronological(async_client, admin_token):
    response = await async_client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]

    monthly_activity = data["monthly_activity"]
    assert monthly_activity["period"] == "last_12_months"
    assert monthly_activity["timezone"] == settings.RESTAURANT_TIMEZONE

    months = monthly_activity["months"]
    assert len(months) == 12

    # Check chronological ordering: each month must be > previous month
    month_strings = [m["month"] for m in months]
    assert month_strings == sorted(month_strings)

    # Current month in restaurant timezone must be the last item
    tz = zoneinfo.ZoneInfo(settings.RESTAURANT_TIMEZONE)
    expected_current_month = datetime.now(tz).strftime("%Y-%m")
    assert month_strings[-1] == expected_current_month


@pytest.mark.asyncio
async def test_dashboard_analytics_privacy_guarantee(async_client, admin_token, mock_db):
    """
    CRITICAL PRIVACY AUDIT:
    Verify that analytics response NEVER leaks customer comments, prompt statements,
    customer contact info, raw IPs, or session tracking tokens.
    """
    now = datetime.now(timezone.utc)
    private_note = "SUPER_SECRET_PRIVATE_CUSTOMER_COMMENT_ABC_123"
    await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].insert_one({
        "session_id": "private-session-xyz",
        "food_rating": 5,
        "service_rating": 5,
        "ambience_rating": 5,
        "overall_experience": "positive",
        "customer_notes": private_note,
        "created_at": now,
    })

    response = await async_client.get(
        "/api/v1/analytics/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    raw_response_text = response.text

    # Response must NOT contain the private customer note or session token
    assert private_note not in raw_response_text
    assert "private-session-xyz" not in raw_response_text
    assert "ip_hash" not in raw_response_text
    assert "user_agent" not in raw_response_text


@pytest.mark.asyncio
async def test_dashboard_legacy_overview_backward_compatibility(async_client, admin_token):
    """Ensure existing /api/v1/analytics/overview endpoint still functions perfectly."""
    response = await async_client.get(
        "/api/v1/analytics/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_qr_scans" in data
    assert "total_feedback_submissions" in data
    assert "google_review_link_clicks" in data
    assert "monthly_activity" in data
    assert len(data["monthly_activity"]) == 12
