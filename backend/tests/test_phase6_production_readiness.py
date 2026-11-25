"""
Phase 6 Production Readiness, Security Audit & Payment Verification Test Suite
Verifies:
1. Server-to-server payment capture verification (captured, authorized, failed, order mismatch)
2. Webhook refund processing (payment.refunded / refund.processed expires active subscriptions)
3. Cookie-based dual authentication (HttpOnly cookie set on login, accepted on /auth/me, cleared on /auth/logout)
4. Production configuration security invariants (weak SECRET_KEY rejection, inactive default subscription)
5. Route-specific rate limiter classification for payment and webhook endpoints
"""

import json
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import Settings, settings
from app.db.collections import COLLECTION_PAYMENT_RECORDS, COLLECTION_SUBSCRIPTION_RECORDS
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.services.payment_adapter import payment_adapter
from app.services.subscription_service import subscription_service


# ==============================================================================
# 1. Server-to-Server Payment Capture Verification Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_server_to_server_payment_captured_success(async_client, auth_headers, mock_db):
    """
    Standard successful renewal:
    Payment provider reports status="captured" matching expected order, amount, currency.
    Subscription is verified and activated.
    """
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["order_id"]
    payment_id = "pay_phase6_captured_123"

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
    assert verify_res.json()["data"]["success"] is True
    assert verify_res.json()["data"]["subscription_status"] == "active"

    # Confirm subscription is active
    status = await subscription_service.get_current_status(mock_db)
    assert status == "active"


@pytest.mark.asyncio
async def test_mock_verified_signature_accepted_when_no_live_keys(async_client, auth_headers, mock_db):
    """
    Verify regression fix:
    When in mock testing mode (no live Razorpay keys), the signature 'mock_verified_signature'
    submitted by the admin frontend renewal UI must be accepted and successfully activate the subscription.
    """
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["order_id"]
    payment_id = "pay_mock_ui_signature_test"

    verify_res = await async_client.post(
        "/api/v1/admin/subscription/verify-payment",
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": "mock_verified_signature",
        },
        headers=auth_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["success"] is True
    assert verify_res.json()["data"]["subscription_status"] == "active"


@pytest.mark.asyncio
async def test_server_to_server_payment_authorized_triggers_capture(async_client, auth_headers, mock_db):
    """
    Authorized payment flow:
    Payment provider initially reports status="authorized".
    Backend server-to-server automatically captures the payment and activates subscription.
    """
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["order_id"]
    payment_id = "pay_phase6_authorized_456"

    # Set mock adapter status to 'authorized'
    payment_adapter.set_mock_payment_status(payment_id, "authorized")

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
    assert verify_res.json()["data"]["success"] is True
    assert verify_res.json()["data"]["subscription_status"] == "active"

    # Clean up mock status
    payment_adapter.clear_mock_payments()


@pytest.mark.asyncio
async def test_server_to_server_payment_failed_rejection(async_client, auth_headers, mock_db):
    """
    Failed payment rejection:
    Even if client submits a signature, if payment provider reports status="failed",
    the transaction is rejected with HTTP 400 and cannot activate the subscription.
    """
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["order_id"]
    payment_id = "pay_phase6_failed_789"

    # Mark as failed in provider lookup
    payment_adapter.set_mock_payment_status(payment_id, "failed")

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
    assert verify_res.status_code == 400
    detail = verify_res.json()["detail"].lower()
    assert "failed" in detail or "capture" in detail

    payment_adapter.clear_mock_payments()


@pytest.mark.asyncio
async def test_server_to_server_payment_order_mismatch_rejection(async_client, auth_headers, mock_db):
    """
    Order mismatch rejection:
    If payment is associated with a different order, reject with HTTP 400.
    """
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    assert order_res.status_code == 200
    order_id = order_res.json()["data"]["order_id"]
    payment_id = "pay_phase6_mismatch_order_999"

    payment_adapter.set_mock_payment_status(payment_id, "captured", order_id="different_order_id_wrong")

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
    assert verify_res.status_code == 400
    detail = verify_res.json()["detail"].lower()
    assert "not associated" in detail or "order" in detail

    payment_adapter.clear_mock_payments()


# ==============================================================================
# 2. Webhook Refund Processing Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_webhook_refund_expires_active_subscription(async_client, auth_headers, mock_db):
    """
    Verify payment.refunded webhook:
    1. Activate a subscription via verified payment.
    2. Deliver payment.refunded webhook from payment gateway.
    3. Payment record is updated to status='refunded'.
    4. Active subscription is immediately expired.
    """
    # 1. First activate subscription
    order_res = await async_client.post("/api/v1/admin/subscription/create-order", headers=auth_headers)
    order_id = order_res.json()["data"]["order_id"]
    payment_id = "pay_phase6_to_be_refunded_101"
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
    assert await subscription_service.get_current_status(mock_db) == "active"

    # 2. Simulate Razorpay payment.refunded webhook event
    webhook_payload = {
        "event": "payment.refunded",
        "entity": "event",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": settings.SUBSCRIPTION_AMOUNT_PAISE,
                    "currency": settings.PAYMENT_CURRENCY,
                    "status": "refunded",
                }
            }
        },
    }

    raw_body = json.dumps(webhook_payload)
    sig = payment_adapter.generate_test_webhook_signature(raw_body.encode())
    webhook_res = await async_client.post(
        "/api/v1/webhook/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "x-razorpay-signature": sig,
        },
    )
    assert webhook_res.status_code == 200
    assert webhook_res.json()["result"]["status"] == "recorded_refund"

    # 3. Verify payment record is marked refunded
    payment_rec = await mock_db[COLLECTION_PAYMENT_RECORDS].find_one({"provider_order_id": order_id})
    assert payment_rec is not None
    assert payment_rec["status"] == "refunded"

    # 4. Verify subscription record is now expired
    sub_status = await subscription_service.get_current_status(mock_db)
    assert sub_status == "expired"


# ==============================================================================
# 3. Dual Authentication (Cookie + Bearer Header) & Logout Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_cookie_authentication_and_logout(async_client):
    """
    Verify complete cookie session lifecycle:
    1. POST /auth/login returns access token AND sets admin_access_token HttpOnly cookie.
    2. GET /auth/me succeeds with ONLY the cookie (no Authorization header).
    3. POST /auth/logout clears the admin_access_token cookie.
    4. Subsequent GET /auth/me fails with HTTP 401.
    """
    # 1. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "aslam",
            "password": "aslam0077",
        },
    )
    assert login_res.status_code == 200
    assert "admin_access_token" in login_res.cookies
    cookie_token = login_res.cookies["admin_access_token"]
    assert len(cookie_token) > 20

    # 2. Access /auth/me with cookie ONLY (no Bearer token)
    me_res = await async_client.get(
        "/api/v1/auth/me",
        cookies={"admin_access_token": cookie_token},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["username"] == "aslam"

    # 3. Logout
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        cookies={"admin_access_token": cookie_token},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["authenticated"] is False

    # 4. Access /auth/me without cookies or header -> Rejected 401
    unauth_res = await async_client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401


# ==============================================================================
# 4. Production Configuration Security Invariants
# ==============================================================================

def test_production_rejects_weak_or_default_secret_key():
    """Production mode must reject default or short SECRET_KEY."""
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="insecure-default-secret-key-change-in-production-min-32-chars-long",
        )

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short-key",
        )


def test_production_enforces_inactive_default_subscription():
    """
    Commercial installation invariant:
    In production, SUBSCRIPTION_STATUS_DEFAULT is forced to 'inactive'
    unless explicitly configured with ALLOW_COMPLIMENTARY_TRIAL=True.
    """
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="production-secure-random-key-with-over-32-characters-minimum!",
        SUBSCRIPTION_STATUS_DEFAULT="active",
        ALLOW_COMPLIMENTARY_TRIAL=False,
    )
    # Default is coerced to inactive for commercial deployment
    assert prod_settings.SUBSCRIPTION_STATUS_DEFAULT == "inactive"
    assert prod_settings.SUBSCRIPTION_REQUIRED is True

    # With explicit complimentary trial
    trial_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="production-secure-random-key-with-over-32-characters-minimum!",
        SUBSCRIPTION_STATUS_DEFAULT="active",
        ALLOW_COMPLIMENTARY_TRIAL=True,
    )
    assert trial_settings.SUBSCRIPTION_STATUS_DEFAULT == "active"


# ==============================================================================
# 5. Route Rate Limiter Bucket Categorization Tests
# ==============================================================================

def test_rate_limiter_categories_and_limits():
    """Verify rate limiter middleware initializes specialized payment and webhook buckets."""
    middleware = RateLimiterMiddleware(app=None)
    assert "payment" in middleware.request_history
    assert "webhook" in middleware.request_history
    assert "scan" in middleware.request_history
    assert "auth" in middleware.request_history
    assert "feedback" in middleware.request_history
    assert "default" in middleware.request_history
