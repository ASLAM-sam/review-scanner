"""
Subscription Lifecycle, Payment Verification, Expiry Enforcement & Permanent QR Test Suite
Single-Tenant Independent Restaurant Deployment
"""

from datetime import datetime, timedelta, timezone
import pytest
from app.core.config import settings
from app.db.collections import COLLECTION_PAYMENT_RECORDS, COLLECTION_SUBSCRIPTION_RECORDS
from app.models.subscription import SubscriptionRecord
from app.services.payment_adapter import payment_adapter
from app.services.subscription_service import add_calendar_month, subscription_service


# ==============================================================================
# 1. Deterministic Calendar Month Arithmetic Tests
# ==============================================================================

def test_calendar_month_arithmetic_standard():
    dt = datetime(2026, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
    res = add_calendar_month(dt)
    assert res.year == 2026
    assert res.month == 4
    assert res.day == 15
    assert res.hour == 10
    assert res.minute == 30


def test_calendar_month_arithmetic_jan_31_to_feb():
    # 2026 is not a leap year -> Feb has 28 days
    dt = datetime(2026, 1, 31, 14, 0, 0, tzinfo=timezone.utc)
    res = add_calendar_month(dt)
    assert res.year == 2026
    assert res.month == 2
    assert res.day == 28


def test_calendar_month_arithmetic_leap_year_feb_29():
    # 2028 is a leap year -> Feb has 29 days
    dt = datetime(2028, 1, 31, 12, 0, 0, tzinfo=timezone.utc)
    res = add_calendar_month(dt)
    assert res.year == 2028
    assert res.month == 2
    assert res.day == 29

    # Feb 29 to March
    res_mar = add_calendar_month(res)
    assert res_mar.year == 2028
    assert res_mar.month == 3
    assert res_mar.day == 29


def test_calendar_month_arithmetic_december_to_january():
    dt = datetime(2026, 12, 10, 8, 0, 0, tzinfo=timezone.utc)
    res = add_calendar_month(dt)
    assert res.year == 2027
    assert res.month == 1
    assert res.day == 10


def test_calendar_month_arithmetic_31_day_to_30_day_month():
    # May 31 to June 30
    dt = datetime(2026, 5, 31, 12, 0, 0, tzinfo=timezone.utc)
    res = add_calendar_month(dt)
    assert res.year == 2026
    assert res.month == 6
    assert res.day == 30


# ==============================================================================
# 2. Permanent QR Code Integrity Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_permanent_qr_integrity_across_subscription_lifecycle(async_client, auth_headers, mock_db):
    """
    CRITICAL TEST:
    The QR code URL must be permanent and identical before expiry, during expiry, and after renewal.
    """
    # 1. Fetch QR details while subscription is initially active
    qr_res_1 = await async_client.get("/api/v1/admin/qr", headers=auth_headers)
    assert qr_res_1.status_code == 200
    qr_data_1 = qr_res_1.json()["data"]
    initial_url = qr_data_1["destination_url"]
    initial_slug = qr_data_1["slug"]

    # 2. Expire the subscription
    past_date = datetime.now(timezone.utc) - timedelta(days=5)
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].delete_many({})
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one({
        "plan_id": settings.SUBSCRIPTION_PLAN_ID,
        "plan_name": settings.SUBSCRIPTION_PLAN_NAME,
        "status": "expired",
        "amount_paise": settings.SUBSCRIPTION_AMOUNT_PAISE,
        "currency": settings.PAYMENT_CURRENCY,
        "billing_interval": "monthly",
        "expires_at": past_date,
        "created_at": past_date,
        "updated_at": past_date,
    })

    # Verify status is expired
    status_str = await subscription_service.get_current_status(mock_db)
    assert status_str == "expired"

    # 3. Check QR details while subscription is expired
    qr_res_2 = await async_client.get("/api/v1/admin/qr", headers=auth_headers)
    assert qr_res_2.status_code == 200
    qr_data_2 = qr_res_2.json()["data"]
    expired_url = qr_data_2["destination_url"]
    expired_slug = qr_data_2["slug"]

    # Must be 100% IDENTICAL
    assert expired_url == initial_url
    assert expired_slug == initial_slug

    # 4. Customer scans expired QR
    scan_res = await async_client.post("/api/v1/public/qr/scan")
    assert scan_res.status_code == 200
    scan_data = scan_res.json()["data"]
    assert scan_data["subscription_status"] == "expired"
    assert scan_data["destination_url"] == initial_url

    # 5. Admin renews subscription
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_data = order_res.json()["data"]
    order_id = order_data["order_id"]
    payment_id = "pay_test_renewal_123"
    valid_sig = payment_adapter.generate_test_signature(order_id, payment_id)

    verify_res = await async_client.post(
        "/api/v1/admin/subscription/verify-payment",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": valid_sig,
        },
        headers=auth_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["subscription_status"] == "active"

    # 6. Check QR details after renewal
    qr_res_3 = await async_client.get("/api/v1/admin/qr", headers=auth_headers)
    assert qr_res_3.status_code == 200
    qr_data_3 = qr_res_3.json()["data"]
    renewed_url = qr_data_3["destination_url"]
    renewed_slug = qr_data_3["slug"]

    # Absolute proof: QR URL has NOT changed
    assert renewed_url == initial_url
    assert renewed_slug == initial_slug

    # Customer scans renewed QR -> active
    scan_res_active = await async_client.post("/api/v1/public/qr/scan")
    assert scan_res_active.status_code == 200
    assert scan_res_active.json()["data"]["subscription_status"] == "active"


# ==============================================================================
# 3. Server-Side Customer API Expiry Enforcement
# ==============================================================================

@pytest.mark.asyncio
async def test_customer_api_blocked_when_subscription_expired(async_client, mock_db):
    """
    Verify that customer endpoints strictly reject access when subscription is expired.
    Direct API requests cannot bypass server-side checks.
    """
    # 1. Force expired state
    past = datetime.now(timezone.utc) - timedelta(days=2)
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].delete_many({})
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one({
        "plan_id": settings.SUBSCRIPTION_PLAN_ID,
        "plan_name": settings.SUBSCRIPTION_PLAN_NAME,
        "status": "expired",
        "amount_paise": settings.SUBSCRIPTION_AMOUNT_PAISE,
        "currency": settings.PAYMENT_CURRENCY,
        "billing_interval": "monthly",
        "expires_at": past,
        "created_at": past,
        "updated_at": past,
    })

    # Public restaurant config returns subscription_status="expired"
    res = await async_client.get("/api/v1/public/restaurant")
    assert res.status_code == 200
    assert res.json()["data"]["subscription_status"] == "expired"

    # Feedback submission is strictly blocked with HTTP 403 SUBSCRIPTION_EXPIRED
    fb_res = await async_client.post(
        "/api/v1/public/feedback",
        json={
            "session_id": "test-session-expired",
            "food_rating": 5,
            "service_rating": 5,
            "ambience_rating": 5,
            "overall_experience": "positive",
        },
    )
    assert fb_res.status_code == 403
    assert "SUBSCRIPTION_EXPIRED" in fb_res.json()["detail"]

    # Review click is strictly blocked with HTTP 403 SUBSCRIPTION_EXPIRED
    click_res = await async_client.post(
        "/api/v1/public/review-click",
        json={"session_id": "test-session-expired"},
    )
    assert click_res.status_code == 403
    assert "SUBSCRIPTION_EXPIRED" in click_res.json()["detail"]

    # Prompts retrieval is strictly blocked with HTTP 403 SUBSCRIPTION_EXPIRED
    prompt_res = await async_client.get("/api/v1/public/prompts")
    assert prompt_res.status_code == 403
    assert "SUBSCRIPTION_EXPIRED" in prompt_res.json()["detail"]


# ==============================================================================
# 4. Admin Access & Renewal Flow During Expiry
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_can_access_and_renew_when_subscription_is_expired(async_client, auth_headers, mock_db):
    """
    Administrators must NOT be locked out when subscription expires.
    Admins can view status and complete renewal.
    """
    past = datetime.now(timezone.utc) - timedelta(days=1)
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].delete_many({})
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one({
        "plan_id": settings.SUBSCRIPTION_PLAN_ID,
        "plan_name": settings.SUBSCRIPTION_PLAN_NAME,
        "status": "expired",
        "amount_paise": settings.SUBSCRIPTION_AMOUNT_PAISE,
        "currency": settings.PAYMENT_CURRENCY,
        "billing_interval": "monthly",
        "expires_at": past,
        "created_at": past,
        "updated_at": past,
    })

    # Admin accesses subscription details
    sub_res = await async_client.get("/api/v1/admin/subscription", headers=auth_headers)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()["data"]
    assert sub_data["status"] == "expired"
    assert sub_data["is_expired"] is True
    assert sub_data["can_renew"] is True
    assert sub_data["amount_paise"] == 24900
    assert sub_data["amount_display"] == "₹249"

    # Admin initiates renewal order
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_data = order_res.json()["data"]
    assert order_data["amount_paise"] == 24900
    assert order_data["currency"] == "INR"

    # Admin verifies payment
    order_id = order_data["order_id"]
    payment_id = "pay_test_expired_renewal"
    signature = payment_adapter.generate_test_signature(order_id, payment_id)

    verify_res = await async_client.post(
        "/api/v1/admin/subscription/verify-payment",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
        headers=auth_headers,
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()["data"]
    assert verify_data["success"] is True
    assert verify_data["subscription_status"] == "active"

    # Verify subscription status is now active in database
    sub_status = await subscription_service.get_current_status(mock_db)
    assert sub_status == "active"


# ==============================================================================
# 5. Payment Security & Tampering Protections
# ==============================================================================

@pytest.mark.asyncio
async def test_invalid_signature_rejected(async_client, auth_headers):
    """Tampered or invalid payment signature must be strictly rejected with HTTP 400."""
    response = await async_client.post(
        "/api/v1/admin/subscription/verify-payment",
        json={
            "razorpay_order_id": "order_test_fake_123",
            "razorpay_payment_id": "pay_test_fake_123",
            "razorpay_signature": "tampered_invalid_signature_hash_xyz",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "verification failed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_verification_is_idempotent(async_client, auth_headers, mock_db):
    """
    Submitting the same verified order twice must NOT extend the subscription period twice.
    """
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_data = order_res.json()["data"]
    order_id = order_data["order_id"]
    payment_id = "pay_idempotency_test_1"
    signature = payment_adapter.generate_test_signature(order_id, payment_id)

    # First verification
    res1 = await async_client.post(
        "/api/v1/admin/subscription/verify-payment",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
        headers=auth_headers,
    )
    assert res1.status_code == 200
    expiry_1 = res1.json()["data"]["expires_at"]

    # Second verification (duplicate request / retry)
    res2 = await async_client.post(
        "/api/v1/admin/subscription/verify-payment",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
        headers=auth_headers,
    )
    assert res2.status_code == 200
    expiry_2 = res2.json()["data"]["expires_at"]

    # Expiry must be identical: no double extension (within 1 second accounting for DB BSON millisecond truncation)
    dt1 = datetime.fromisoformat(expiry_1.replace("Z", "+00:00"))
    dt2 = datetime.fromisoformat(expiry_2.replace("Z", "+00:00"))
    assert abs((dt1 - dt2).total_seconds()) < 1.0


@pytest.mark.asyncio
async def test_early_renewal_extends_from_existing_expiry(async_client, auth_headers, mock_db):
    """
    When renewing early before expiry, the subscription period must extend from the
    existing expiry date, NOT from the current moment (which would shorten the paid duration).
    """
    now = datetime.now(timezone.utc)
    # Existing subscription expires in 15 days
    existing_expiry = now + timedelta(days=15)
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].delete_many({})
    await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one({
        "plan_id": settings.SUBSCRIPTION_PLAN_ID,
        "plan_name": settings.SUBSCRIPTION_PLAN_NAME,
        "status": "active",
        "amount_paise": settings.SUBSCRIPTION_AMOUNT_PAISE,
        "currency": settings.PAYMENT_CURRENCY,
        "billing_interval": "monthly",
        "started_at": now - timedelta(days=15),
        "current_period_start": now - timedelta(days=15),
        "current_period_end": existing_expiry,
        "expires_at": existing_expiry,
        "created_at": now - timedelta(days=15),
        "updated_at": now,
    })

    # Create and verify renewal
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    order_id = order_res.json()["data"]["order_id"]
    payment_id = "pay_early_renewal_test"
    signature = payment_adapter.generate_test_signature(order_id, payment_id)

    verify_res = await async_client.post(
        "/api/v1/admin/subscription/verify-payment",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
        headers=auth_headers,
    )
    assert verify_res.status_code == 200
    new_expiry_str = verify_res.json()["data"]["expires_at"]
    new_expiry = datetime.fromisoformat(new_expiry_str.replace("Z", "+00:00"))

    # Expected new expiry: 1 calendar month added to the existing_expiry
    expected_expiry = add_calendar_month(existing_expiry)
    assert abs((new_expiry - expected_expiry).total_seconds()) < 5


# ==============================================================================
# 6. Webhook Processing Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_webhook_payment_captured_success(async_client, mock_db):
    """Valid signed payment.captured webhook activates subscription."""
    import json
    order_id = "order_webhook_test_101"
    payment_id = "pay_webhook_test_101"
    payload = {
        "event": "payment.captured",
        "id": "evt_test_101",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": 24900,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = payment_adapter.generate_test_webhook_signature(raw_body)

    res = await async_client.post(
        "/api/v1/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )
    assert res.status_code == 200
    assert res.json()["result"]["status"] == "success"

    # Verify subscription is now active in database
    status_str = await subscription_service.get_current_status(mock_db)
    assert status_str == "active"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_rejected(async_client):
    """Webhook with invalid signature must be rejected with HTTP 400."""
    import json
    payload = {"event": "payment.captured", "id": "evt_fake"}
    raw_body = json.dumps(payload).encode("utf-8")

    res = await async_client.post(
        "/api/v1/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "invalid_signature_tampered",
        },
    )
    assert res.status_code == 400
    assert "invalid webhook signature" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_amount_mismatch_rejected(async_client, mock_db):
    """Webhook with tampered payment amount must be rejected."""
    import json
    payload = {
        "event": "payment.captured",
        "id": "evt_amount_mismatch",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_tampered_1",
                    "order_id": "order_tampered_1",
                    "amount": 100,  # Only ₹1 instead of ₹249
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = payment_adapter.generate_test_webhook_signature(raw_body)

    res = await async_client.post(
        "/api/v1/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )
    assert res.status_code == 200
    assert res.json()["result"]["status"] == "error"
    assert res.json()["result"]["reason"] == "amount_mismatch"


# ==============================================================================
# 7. Payment History & Audit Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_payment_history_audit(async_client, auth_headers, mock_db):
    """Admin can view payment transaction history."""
    now = datetime.now(timezone.utc)
    await mock_db[COLLECTION_PAYMENT_RECORDS].insert_one({
        "payment_id": "pay_history_1",
        "payment_provider": "razorpay",
        "provider_order_id": "order_history_1",
        "provider_payment_id": "pay_rzp_history_1",
        "amount_paise": 24900,
        "currency": "INR",
        "status": "verified",
        "created_at": now,
        "verified_at": now,
    })

    res = await async_client.get("/api/v1/admin/subscription/payments", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert data["payments"][0]["payment_id"] == "pay_history_1"
    assert data["payments"][0]["amount_display"] == "₹249"
    assert data["payments"][0]["status"] == "verified"
