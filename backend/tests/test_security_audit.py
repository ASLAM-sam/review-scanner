"""
Phase 1.5 Security Audit Test Suite
Verifies:
- Token expiration & invalid signature rejection
- Inactive user authorization rejection
- Open redirect & URL injection prevention on review click
- Feedback submission deduplication & idempotency
- Bot/crawler filtering & scan reload deduplication
- Request body size limit enforcement
- Security headers (CSP, HSTS, X-Frame, X-Content-Type)
"""

from datetime import datetime, timedelta, timezone
import pytest
import jwt
from app.core.config import settings
from app.core.security import create_access_token
from app.db.collections import (
    COLLECTION_ADMIN_USERS,
    COLLECTION_FEEDBACK_SUBMISSIONS,
    COLLECTION_QR_SCANS,
    COLLECTION_REVIEW_LINK_CLICKS,
)
from app.models.user import AdminUserInDB
from app.services.qr_service import qr_service


@pytest.mark.asyncio
async def test_expired_token_rejection(async_client):
    """Verify expired JWT tokens are explicitly rejected with 401."""
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    expired_payload = {
        "sub": "testadmin@restaurant.com",
        "exp": past,
        "iat": past - timedelta(minutes=30),
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tampered_token_signature_rejection(async_client):
    """Verify tokens signed with a different key are rejected with 401."""
    fake_token = jwt.encode(
        {"sub": "testadmin@restaurant.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "completely-different-signing-key-12345678",
        algorithm="HS256",
    )
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_admin_account_rejected(async_client, mock_db):
    """Verify deactivated admin accounts cannot access protected endpoints."""
    # Insert deactivated admin
    inactive_user = AdminUserInDB(
        email="inactive@restaurant.com",
        hashed_password="hashed_pw_dummy",
        full_name="Inactive Admin",
        is_active=False,
    )
    await mock_db[COLLECTION_ADMIN_USERS].insert_one(
        inactive_user.model_dump(by_alias=False, exclude={"id"})
    )

    token = create_access_token(data={"sub": "inactive@restaurant.com"})
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_open_redirect_protection_on_review_click(async_client, mock_db):
    """
    Verify client cannot pass arbitrary malicious URLs to /review-click.
    Target URL must strictly be the server-configured Google Review URL.
    """
    click_payload = {
        "session_id": "test-session-security",
        "target_url": "https://malicious-phishing-attacker.com/steal-creds",
    }
    response = await async_client.post("/api/v1/public/review-click", json=click_payload)
    assert response.status_code == 200
    returned_url = response.json()["data"]["target_url"]

    # Must NOT equal the malicious URL!
    assert returned_url != "https://malicious-phishing-attacker.com/steal-creds"
    assert returned_url == "https://g.page/r/test-review"

    # Verify database also stored the authoritative URL, not the attacker URL
    recorded = await mock_db[COLLECTION_REVIEW_LINK_CLICKS].find_one(
        {"session_id": "test-session-security"}
    )
    assert recorded is not None
    assert recorded["target_url"] == "https://g.page/r/test-review"


@pytest.mark.asyncio
async def test_feedback_idempotency_prevents_duplicate_submissions(async_client, mock_db):
    """Verify multiple feedback submissions with same session_id do not create duplicate records."""
    session_id = "test-session-idempotent-1"

    feedback_data = {
        "session_id": session_id,
        "food_rating": 5,
        "service_rating": 5,
        "ambience_rating": 4,
        "overall_experience": "positive",
        "customer_notes": "First submission",
    }

    # 1. First submission succeeds
    res1 = await async_client.post("/api/v1/public/feedback", json=feedback_data)
    assert res1.status_code == 200

    # 2. Duplicate submission with same session_id
    feedback_data["customer_notes"] = "Duplicate spam submission attempt"
    res2 = await async_client.post("/api/v1/public/feedback", json=feedback_data)
    assert res2.status_code == 200

    # Verify only ONE document exists in DB for this session
    count = await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].count_documents({"session_id": session_id})
    assert count == 1


@pytest.mark.asyncio
async def test_crawler_and_bot_detection_on_qr_scan(async_client, mock_db):
    """Verify search engine bots and crawlers are tagged as bots and not counted as unique human scans."""
    bot_ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    response = await async_client.post(
        "/api/v1/public/qr/scan",
        headers={"User-Agent": bot_ua},
    )
    assert response.status_code == 200
    session_id = response.json()["data"]["session_id"]

    # Verify document in DB has is_bot=True and is_unique=False
    scan_doc = await mock_db[COLLECTION_QR_SCANS].find_one({"session_id": session_id})
    assert scan_doc is not None
    assert scan_doc["is_bot"] is True
    assert scan_doc["is_unique"] is False


@pytest.mark.asyncio
async def test_browser_refresh_scan_deduplication(async_client, mock_db):
    """Verify page reloads with same session_id are flagged as is_unique=False."""
    # 1. First scan
    res1 = await async_client.post("/api/v1/public/qr/scan", json={})
    session_id = res1.json()["data"]["session_id"]

    # 2. Reload with same session_id
    res2 = await async_client.post("/api/v1/public/qr/scan", json={"session_id": session_id})
    assert res2.status_code == 200

    scans = await mock_db[COLLECTION_QR_SCANS].find({"session_id": session_id}).to_list(10)
    assert len(scans) == 2
    # First is unique
    assert scans[0]["is_unique"] is True
    # Reload is not unique
    assert scans[1]["is_unique"] is False


@pytest.mark.asyncio
async def test_security_headers_present_on_all_responses(async_client):
    """Verify OWASP defensive headers are present."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in headers
    assert "Strict-Transport-Security" in headers
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_oversized_payload_rejected(async_client):
    """Verify payload exceeding MAX_REQUEST_BODY_SIZE is rejected with 413."""
    oversized_data = {"data": "x" * (settings.MAX_REQUEST_BODY_SIZE + 500)}
    response = await async_client.post(
        "/api/v1/public/feedback",
        json=oversized_data,
        headers={"Content-Length": str(settings.MAX_REQUEST_BODY_SIZE + 500)},
    )
    assert response.status_code == 413

