"""
Payment Gateway Adapter Module
Isolates Razorpay provider API, HMAC-SHA256 signature verification, and webhook validation.
Single-Tenant Independent Restaurant Deployment
"""

import hashlib
import hmac
import uuid
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger


class PaymentAdapterError(Exception):
    """Base exception for payment gateway operations."""
    pass


class PaymentSignatureVerificationError(PaymentAdapterError):
    """Raised when cryptographic signature check fails."""
    pass


class PaymentAdapter:
    """
    Adapter for Payment Gateway interactions.
    Strictly isolated behind standard interfaces to keep business logic decoupled from provider.
    """

    RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
    _mock_payment_status_override: Dict[str, str] = {}
    _mock_payments_db: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def is_live_configured(cls) -> bool:
        """Check if production/live Razorpay credentials are configured."""
        return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)

    @classmethod
    async def create_order(
        cls,
        amount_paise: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a payment order with the gateway.
        Never trust client-side amounts. Always uses server-side configured paise.
        """
        effective_receipt = receipt or f"rcpt_{uuid.uuid4().hex[:12]}"
        effective_notes = notes or {}

        # 1. Live Razorpay API call if credentials configured
        if cls.is_live_configured():
            try:
                auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                payload = {
                    "amount": amount_paise,
                    "currency": currency,
                    "receipt": effective_receipt,
                    "notes": effective_notes,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{cls.RAZORPAY_API_BASE}/orders",
                        auth=auth,
                        json=payload,
                    )
                    if resp.status_code != 200:
                        logger.error(f"Razorpay order creation failed: {resp.status_code} - {resp.text}")
                        raise PaymentAdapterError(f"Payment gateway error: {resp.text}")
                    data = resp.json()
                    return {
                        "order_id": data["id"],
                        "amount": data["amount"],
                        "currency": data["currency"],
                        "receipt": data.get("receipt", effective_receipt),
                        "status": data.get("status", "created"),
                        "key_id": settings.RAZORPAY_KEY_ID,
                    }
            except Exception as exc:
                if isinstance(exc, PaymentAdapterError):
                    raise
                logger.error(f"Exception connecting to Razorpay: {exc}")
                raise PaymentAdapterError(f"Failed to communicate with payment provider: {exc}")

        # 2. Mock mode for automated testing / sandbox when keys are empty
        logger.info("Running in mock payment mode (no live Razorpay API keys configured).")
        mock_order_id = f"order_mock_{uuid.uuid4().hex[:16]}"
        return {
            "order_id": mock_order_id,
            "amount": amount_paise,
            "currency": currency,
            "receipt": effective_receipt,
            "status": "created",
            "key_id": settings.RAZORPAY_KEY_ID or "rzp_test_mock_key",
        }

    @classmethod
    async def fetch_payment(
        cls,
        payment_id: str,
        expected_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify payment state directly with payment provider server-to-server.
        CRITICAL FOR STAGE 3: Signature verification alone does not prove capture.
        """
        if cls.is_live_configured():
            try:
                auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{cls.RAZORPAY_API_BASE}/payments/{payment_id}",
                        auth=auth,
                    )
                    if resp.status_code != 200:
                        logger.error(f"Razorpay payment fetch failed: {resp.status_code} - {resp.text}")
                        raise PaymentAdapterError(f"Failed to fetch payment details from provider: {resp.text}")
                    data = resp.json()
                    return {
                        "id": data["id"],
                        "order_id": data.get("order_id"),
                        "amount": data.get("amount"),
                        "currency": data.get("currency"),
                        "status": data.get("status"),  # 'captured', 'authorized', 'failed', 'refunded'
                        "method": data.get("method"),
                    }
            except Exception as exc:
                if isinstance(exc, PaymentAdapterError):
                    raise
                logger.error(f"Exception fetching payment from Razorpay: {exc}")
                raise PaymentAdapterError(f"Provider payment lookup failed: {exc}")

        # In mock mode, check if a status override was configured for testing
        status = cls._mock_payment_status_override.get(payment_id, "captured")
        mock_data = cls._mock_payments_db.get(payment_id, {})
        return {
            "id": payment_id,
            "order_id": mock_data.get("order_id", expected_order_id or "order_mock"),
            "amount": mock_data.get("amount", settings.SUBSCRIPTION_AMOUNT_PAISE),
            "currency": mock_data.get("currency", settings.PAYMENT_CURRENCY),
            "status": status,
            "method": "mock_card",
        }

    @classmethod
    async def capture_payment(
        cls,
        payment_id: str,
        amount_paise: int,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        """
        Capture an authorized payment with Razorpay server-to-server.
        """
        if cls.is_live_configured():
            try:
                auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                payload = {"amount": amount_paise, "currency": currency}
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{cls.RAZORPAY_API_BASE}/payments/{payment_id}/capture",
                        auth=auth,
                        json=payload,
                    )
                    if resp.status_code != 200:
                        logger.error(f"Razorpay payment capture failed: {resp.status_code} - {resp.text}")
                        raise PaymentAdapterError(f"Payment capture failed: {resp.text}")
                    data = resp.json()
                    return {
                        "id": data["id"],
                        "status": data.get("status", "captured"),
                        "amount": data.get("amount"),
                        "currency": data.get("currency"),
                    }
            except Exception as exc:
                if isinstance(exc, PaymentAdapterError):
                    raise
                logger.error(f"Exception capturing Razorpay payment: {exc}")
                raise PaymentAdapterError(f"Failed to capture payment with provider: {exc}")

        cls._mock_payment_status_override[payment_id] = "captured"
        return {
            "id": payment_id,
            "status": "captured",
            "amount": amount_paise,
            "currency": currency,
        }

    @classmethod
    def set_mock_payment_status(cls, payment_id: str, status: str, order_id: Optional[str] = None, amount: Optional[int] = None):
        """Test fixture helper to simulate different provider states (captured, authorized, failed, refunded)."""
        cls._mock_payment_status_override[payment_id] = status
        if order_id or amount:
            cls._mock_payments_db[payment_id] = {
                "order_id": order_id,
                "amount": amount,
                "currency": settings.PAYMENT_CURRENCY,
            }

    @classmethod
    def clear_mock_payments(cls):
        """Reset mock payment overrides."""
        cls._mock_payment_status_override.clear()
        cls._mock_payments_db.clear()

    @classmethod
    def verify_payment_signature(
        cls,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """
        Verify the Razorpay payment signature received after browser checkout.
        Formula: HMAC-SHA256(order_id + "|" + payment_id, key_secret) == signature
        """
        if not order_id or not payment_id or not signature:
            return False

        secret = settings.RAZORPAY_KEY_SECRET

        # If in mock testing mode without keys, accept test signature
        if not secret:
            if signature == "mock_verified_signature":
                return True
            secret = "mock_secret_key_for_testing_purposes"
            # Allow predictable test mock signature
            expected_mock = hmac.new(
                secret.encode("utf-8"),
                f"{order_id}|{payment_id}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected_mock, signature)

        try:
            expected_signature = hmac.new(
                secret.encode("utf-8"),
                f"{order_id}|{payment_id}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as exc:
            logger.error(f"Error verifying payment signature: {exc}")
            return False

    @classmethod
    def verify_webhook_signature(
        cls,
        raw_body: bytes,
        signature: Optional[str],
    ) -> bool:
        """
        Verify Razorpay Webhook signature against raw request body bytes.
        Formula: HMAC-SHA256(raw_body, webhook_secret) == X-Razorpay-Signature
        """
        if not raw_body or not signature:
            return False

        secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not secret:
            secret = "mock_webhook_secret_for_testing"

        try:
            expected_signature = hmac.new(
                secret.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as exc:
            logger.error(f"Error verifying webhook signature: {exc}")
            return False

    @classmethod
    def generate_test_signature(cls, order_id: str, payment_id: str, secret: Optional[str] = None) -> str:
        """Utility for test suites to generate a mathematically valid signature."""
        effective_secret = secret or settings.RAZORPAY_KEY_SECRET or "mock_secret_key_for_testing_purposes"
        return hmac.new(
            effective_secret.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    def generate_test_webhook_signature(cls, body_bytes: bytes, secret: Optional[str] = None) -> str:
        """Utility for test suites to generate a mathematically valid webhook signature."""
        effective_secret = secret or settings.RAZORPAY_WEBHOOK_SECRET or "mock_webhook_secret_for_testing"
        return hmac.new(
            effective_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()


payment_adapter = PaymentAdapter()
