"""
Subscription Management Service
Handles subscription lifecycle, payment verification, calendar month calculation,
expiry enforcement, and permanent QR state preservation.
Single-Tenant Independent Restaurant Deployment
"""

import calendar
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import logger
from app.db.collections import COLLECTION_PAYMENT_RECORDS, COLLECTION_SUBSCRIPTION_RECORDS
from app.models.payment import PaymentRecord
from app.models.subscription import SubscriptionRecord
from app.schemas.subscription import (
    CreateOrderResponse,
    PaymentHistoryItem,
    PaymentHistoryResponse,
    SubscriptionStatusResponse,
    VerifyPaymentResponse,
)
from app.services.payment_adapter import payment_adapter
from app.services.restaurant_service import restaurant_service


def add_calendar_month(dt: datetime) -> datetime:
    """
    Deterministic calendar month addition.
    Handles variable month lengths and month-end dates correctly.
    E.g.
      Jan 31 -> Feb 28 (or Feb 29 on leap year)
      Jan 30 -> Feb 28
      March 31 -> April 30
      August 31 -> September 30
    Preserves exact hour, minute, second, and tzinfo.
    """
    year = dt.year
    month = dt.month + 1
    if month > 12:
        year += 1
        month = 1
    _, max_days = calendar.monthrange(year, month)
    day = min(dt.day, max_days)
    return dt.replace(year=year, month=month, day=day)


class SubscriptionService:
    @staticmethod
    def format_amount_display(amount_paise: int, currency: str = "INR") -> str:
        """Format integer paise into customer-facing currency string, e.g. 24900 -> '₹249'."""
        rupees = amount_paise // 100
        if currency == "INR":
            return f"₹{rupees}"
        return f"{currency} {rupees}"

    @classmethod
    async def get_latest_subscription(
        cls, db: Optional[AsyncIOMotorDatabase]
    ) -> Optional[SubscriptionRecord]:
        """Fetch the latest subscription record for this installation."""
        if db is None:
            return None
        doc = await db[COLLECTION_SUBSCRIPTION_RECORDS].find_one(
            sort=[("created_at", -1)]
        )
        if not doc:
            return None
        return SubscriptionRecord(**doc)

    @classmethod
    async def ensure_initial_subscription(
        cls, db: Optional[AsyncIOMotorDatabase]
    ) -> SubscriptionRecord:
        """
        Ensure an initial subscription record exists on fresh deployment.
        If none exists, create default standard monthly record.
        """
        existing = await cls.get_latest_subscription(db)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        # Default initial expiry: 30 days from now if active default, or now if inactive
        expires_at = add_calendar_month(now) if settings.SUBSCRIPTION_STATUS_DEFAULT == "active" else now
        sub = SubscriptionRecord(
            plan_id=settings.SUBSCRIPTION_PLAN_ID,
            plan_name=settings.SUBSCRIPTION_PLAN_NAME,
            status=settings.SUBSCRIPTION_STATUS_DEFAULT,
            amount_paise=settings.SUBSCRIPTION_AMOUNT_PAISE,
            currency=settings.PAYMENT_CURRENCY,
            billing_interval=settings.SUBSCRIPTION_BILLING_INTERVAL,
            started_at=now if settings.SUBSCRIPTION_STATUS_DEFAULT == "active" else None,
            current_period_start=now if settings.SUBSCRIPTION_STATUS_DEFAULT == "active" else None,
            current_period_end=expires_at,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        if db is not None:
            await db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one(
                sub.model_dump(by_alias=False, exclude={"id"})
            )
            logger.info("Initialized default subscription record for restaurant installation.")
        return sub

    @classmethod
    async def get_current_status(cls, db: Optional[AsyncIOMotorDatabase]) -> str:
        """
        Get current subscription status: 'active', 'expired', 'inactive', 'pending', 'cancelled'.
        Server-side expiry evaluation with zero grace period by default.
        """
        if not settings.SUBSCRIPTION_REQUIRED:
            return settings.SUBSCRIPTION_STATUS_DEFAULT

        if db is None:
            return settings.SUBSCRIPTION_STATUS_DEFAULT

        try:
            sub = await cls.get_latest_subscription(db)
            if not sub:
                sub = await cls.ensure_initial_subscription(db)

            now = datetime.now(timezone.utc)
            expiry_date = sub.expires_at
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)

            # Apply configurable grace period (default 0 days)
            grace_boundary = expiry_date + timedelta(days=settings.SUBSCRIPTION_GRACE_DAYS)

            if now >= grace_boundary:
                # Subscription has expired
                if sub.status == "active":
                    # Update database state to expired
                    await db[COLLECTION_SUBSCRIPTION_RECORDS].update_one(
                        {"_id": sub.id} if sub.id else {"created_at": sub.created_at},
                        {"$set": {"status": "expired", "updated_at": now}},
                    )
                return "expired"

            return sub.status
        except Exception as exc:
            logger.warning(f"Error checking subscription status: {exc}")
            return "active"

    @classmethod
    async def is_active(cls, db: Optional[AsyncIOMotorDatabase]) -> bool:
        """Centralized boolean check for whether customer feedback services can operate."""
        status_str = await cls.get_current_status(db)
        return status_str == "active"

    @classmethod
    async def get_subscription_details(
        cls, db: Optional[AsyncIOMotorDatabase]
    ) -> SubscriptionStatusResponse:
        """Retrieve full subscription status and billing information for admin portal."""
        sub = await cls.ensure_initial_subscription(db)
        current_status = await cls.get_current_status(db)

        now = datetime.now(timezone.utc)
        expiry_date = sub.expires_at
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)

        is_expired = (current_status == "expired") or (now >= expiry_date)
        remaining_seconds = max(0, int((expiry_date - now).total_seconds()))
        remaining_days = remaining_seconds // 86400

        return SubscriptionStatusResponse(
            status=current_status,
            plan_id=sub.plan_id or settings.SUBSCRIPTION_PLAN_ID,
            plan_name=sub.plan_name or settings.SUBSCRIPTION_PLAN_NAME,
            amount_paise=settings.SUBSCRIPTION_AMOUNT_PAISE,
            amount_display=cls.format_amount_display(settings.SUBSCRIPTION_AMOUNT_PAISE, settings.PAYMENT_CURRENCY),
            currency=settings.PAYMENT_CURRENCY,
            billing_interval=settings.SUBSCRIPTION_BILLING_INTERVAL,
            started_at=sub.started_at,
            current_period_start=sub.current_period_start,
            current_period_end=sub.current_period_end,
            expires_at=expiry_date,
            remaining_days=remaining_days,
            is_expired=is_expired,
            can_renew=True,
        )

    @classmethod
    async def create_renewal_order(
        cls,
        db: Optional[AsyncIOMotorDatabase],
        admin_email: str,
        idempotency_key: Optional[str] = None,
    ) -> CreateOrderResponse:
        """
        Create a payment order for subscription renewal.
        SECURITY: Amount and currency are strictly taken from server configuration.
        """
        # 1. Idempotency check: if existing pending order with same idempotency key exists, return it
        if db is not None and idempotency_key:
            existing_payment = await db[COLLECTION_PAYMENT_RECORDS].find_one(
                {"idempotency_key": idempotency_key, "status": "created"}
            )
            if existing_payment:
                restaurant = await restaurant_service.get_settings(db)
                return CreateOrderResponse(
                    order_id=existing_payment["provider_order_id"],
                    amount_paise=existing_payment["amount_paise"],
                    currency=existing_payment["currency"],
                    key_id=settings.RAZORPAY_KEY_ID or "rzp_test_mock_key",
                    restaurant_name=restaurant.name,
                    plan_name=settings.SUBSCRIPTION_PLAN_NAME,
                    payment_id=existing_payment["payment_id"],
                )

        restaurant = await restaurant_service.get_settings(db)
        amount_paise = settings.SUBSCRIPTION_AMOUNT_PAISE
        currency = settings.PAYMENT_CURRENCY
        internal_payment_id = f"pay_{uuid.uuid4().hex[:16]}"
        receipt = f"rcpt_{uuid.uuid4().hex[:10]}"

        notes = {
            "restaurant_slug": restaurant.slug,
            "restaurant_name": restaurant.name,
            "admin_email": admin_email,
            "plan_id": settings.SUBSCRIPTION_PLAN_ID,
            "internal_payment_id": internal_payment_id,
        }

        # 2. Create order via payment adapter
        order_data = await payment_adapter.create_order(
            amount_paise=amount_paise,
            currency=currency,
            receipt=receipt,
            notes=notes,
        )

        # 3. Persist payment audit record
        payment_doc = PaymentRecord(
            payment_id=internal_payment_id,
            payment_provider=settings.PAYMENT_PROVIDER,
            provider_order_id=order_data["order_id"],
            amount_paise=amount_paise,
            currency=currency,
            status="created",
            idempotency_key=idempotency_key,
        )

        if db is not None:
            await db[COLLECTION_PAYMENT_RECORDS].insert_one(
                payment_doc.model_dump(by_alias=False, exclude={"id"})
            )
            logger.info(
                f"Created renewal order {order_data['order_id']} for {restaurant.name} (Amount: {amount_paise} paise)"
            )

        return CreateOrderResponse(
            order_id=order_data["order_id"],
            amount_paise=amount_paise,
            currency=currency,
            key_id=order_data.get("key_id", settings.RAZORPAY_KEY_ID or "rzp_test_mock_key"),
            restaurant_name=restaurant.name,
            plan_name=settings.SUBSCRIPTION_PLAN_NAME,
            payment_id=internal_payment_id,
        )

    @classmethod
    async def verify_and_activate(
        cls,
        db: Optional[AsyncIOMotorDatabase],
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> VerifyPaymentResponse:
        """
        Verify payment signature and activate or extend the restaurant's subscription.
        Guarantees idempotency: duplicate calls will not extend the subscription twice.
        """
        # 1. Cryptographic signature check
        is_valid = payment_adapter.verify_payment_signature(
            order_id=order_id,
            payment_id=payment_id,
            signature=signature,
        )
        if not is_valid:
            if db is not None:
                await db[COLLECTION_PAYMENT_RECORDS].update_one(
                    {"provider_order_id": order_id},
                    {
                        "$set": {
                            "status": "failed",
                            "failure_reason": "Invalid payment signature",
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                )
            logger.warning(f"Payment verification failed for order {order_id}: Invalid signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed. Transaction was not verified.",
            )

        # 2. Establish actual provider payment capture state server-to-server (Stage 3 Requirement)
        provider_payment = await payment_adapter.fetch_payment(payment_id, expected_order_id=order_id)

        # Verify provider order_id matches
        if provider_payment.get("order_id") and provider_payment["order_id"] != order_id:
            logger.error(f"Provider payment order mismatch: expected {order_id}, got {provider_payment.get('order_id')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment is not associated with this renewal order.",
            )

        # Verify amount matches configured plan
        if provider_payment.get("amount") is not None and provider_payment["amount"] != settings.SUBSCRIPTION_AMOUNT_PAISE:
            logger.error(f"Payment amount mismatch: expected {settings.SUBSCRIPTION_AMOUNT_PAISE}, got {provider_payment.get('amount')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount does not match subscription plan.",
            )

        # Verify currency matches
        if provider_payment.get("currency") and provider_payment["currency"] != settings.PAYMENT_CURRENCY:
            logger.error(f"Payment currency mismatch: expected {settings.PAYMENT_CURRENCY}, got {provider_payment.get('currency')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment currency does not match subscription plan.",
            )

        # Verify payment status is 'captured' (if 'authorized', attempt capture)
        payment_status = provider_payment.get("status")
        if payment_status == "authorized":
            logger.info(f"Payment {payment_id} is authorized; attempting server-side capture...")
            capture_res = await payment_adapter.capture_payment(
                payment_id=payment_id,
                amount_paise=settings.SUBSCRIPTION_AMOUNT_PAISE,
                currency=settings.PAYMENT_CURRENCY,
            )
            payment_status = capture_res.get("status", "captured")

        if payment_status != "captured":
            logger.warning(f"Payment {payment_id} is not captured with provider (status: {payment_status}).")
            if db is not None:
                await db[COLLECTION_PAYMENT_RECORDS].update_one(
                    {"provider_order_id": order_id},
                    {
                        "$set": {
                            "status": "failed",
                            "failure_reason": f"Payment not captured by provider (Status: {payment_status})",
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment has not been captured by provider (Status: {payment_status}). Subscription cannot be activated.",
            )

        now = datetime.now(timezone.utc)

        # 2. Check existing payment record for idempotency
        if db is not None:
            payment_record = await db[COLLECTION_PAYMENT_RECORDS].find_one(
                {"provider_order_id": order_id}
            )
            if payment_record and payment_record.get("status") == "verified":
                logger.info(f"Payment {order_id} already verified. Returning existing subscription state (Idempotent).")
                latest_sub = await cls.get_latest_subscription(db)
                ret_expires = latest_sub.expires_at if latest_sub else add_calendar_month(now)
                if ret_expires.tzinfo is None:
                    ret_expires = ret_expires.replace(tzinfo=timezone.utc)
                return VerifyPaymentResponse(
                    success=True,
                    status="verified",
                    subscription_status="active",
                    expires_at=ret_expires,
                    message="Payment already verified and subscription is active.",
                )

        # 3. Determine new subscription expiry period
        current_sub = await cls.get_latest_subscription(db) if db is not None else None
        
        # If currently active and unexpired, extend from existing expires_at
        if current_sub and current_sub.status == "active":
            existing_expiry = current_sub.expires_at
            if existing_expiry.tzinfo is None:
                existing_expiry = existing_expiry.replace(tzinfo=timezone.utc)
            if existing_expiry > now:
                new_start = current_sub.current_period_start or now
                new_expiry = add_calendar_month(existing_expiry)
            else:
                new_start = now
                new_expiry = add_calendar_month(now)
        else:
            # Expired or new subscription: starts now and runs for 1 calendar month
            new_start = now
            new_expiry = add_calendar_month(now)

        # 4. Atomic database update: mark payment verified & activate subscription
        if db is not None:
            # Update payment record
            await db[COLLECTION_PAYMENT_RECORDS].update_one(
                {"provider_order_id": order_id},
                {
                    "$set": {
                        "provider_payment_id": payment_id,
                        "provider_signature": signature,
                        "status": "verified",
                        "verified_at": now,
                    }
                },
                upsert=True,
            )

            # Insert/Update subscription record
            new_sub = SubscriptionRecord(
                plan_id=settings.SUBSCRIPTION_PLAN_ID,
                plan_name=settings.SUBSCRIPTION_PLAN_NAME,
                status="active",
                amount_paise=settings.SUBSCRIPTION_AMOUNT_PAISE,
                currency=settings.PAYMENT_CURRENCY,
                billing_interval=settings.SUBSCRIPTION_BILLING_INTERVAL,
                started_at=current_sub.started_at if current_sub and current_sub.started_at else now,
                current_period_start=new_start,
                current_period_end=new_expiry,
                expires_at=new_expiry,
                last_payment_id=payment_id,
                created_at=now,
                updated_at=now,
            )
            await db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one(
                new_sub.model_dump(by_alias=False, exclude={"id"})
            )
            logger.info(
                f"Subscription successfully activated/extended for order {order_id}. "
                f"New Expiry: {new_expiry.isoformat()}"
            )

        return VerifyPaymentResponse(
            success=True,
            status="verified",
            subscription_status="active",
            expires_at=new_expiry,
            message="Payment successfully verified. Subscription is active and QR code is live.",
        )

    @classmethod
    async def process_webhook(
        cls,
        db: Optional[AsyncIOMotorDatabase],
        raw_body: bytes,
        signature: Optional[str],
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process incoming Razorpay webhook delivery.
        Strictly verifies HMAC-SHA256 signature and handles duplicate events idempotently.
        """
        # 1. Verify webhook signature
        is_valid = payment_adapter.verify_webhook_signature(raw_body, signature)
        if not is_valid:
            logger.warning("Rejected webhook: Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature",
            )

        event_name = event_data.get("event")
        event_id = event_data.get("id") or str(uuid.uuid4())
        logger.info(f"Processing webhook event: {event_name} (ID: {event_id})")

        # Handle 'payment.captured' or 'order.paid'
        if event_name in ("payment.captured", "order.paid"):
            payload_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payload_entity.get("order_id")
            payment_id = payload_entity.get("id")
            amount = payload_entity.get("amount")
            currency = payload_entity.get("currency")

            if not order_id or not payment_id:
                logger.warning("Webhook event missing order_id or payment_id")
                return {"status": "ignored", "reason": "missing_identifiers"}

            # Validate amount and currency
            if amount is not None and amount != settings.SUBSCRIPTION_AMOUNT_PAISE:
                logger.error(
                    f"Webhook payment amount mismatch: expected {settings.SUBSCRIPTION_AMOUNT_PAISE}, got {amount}"
                )
                return {"status": "error", "reason": "amount_mismatch"}

            if currency and currency != settings.PAYMENT_CURRENCY:
                logger.error(
                    f"Webhook currency mismatch: expected {settings.PAYMENT_CURRENCY}, got {currency}"
                )
                return {"status": "error", "reason": "currency_mismatch"}

            # Idempotency check: see if event already recorded
            if db is not None:
                existing = await db[COLLECTION_PAYMENT_RECORDS].find_one(
                    {"provider_order_id": order_id}
                )
                if existing and event_id in existing.get("webhook_events", []):
                    logger.info(f"Webhook event {event_id} already processed. Skipping.")
                    return {"status": "already_processed"}

                # Record event ID in payment record
                await db[COLLECTION_PAYMENT_RECORDS].update_one(
                    {"provider_order_id": order_id},
                    {"$addToSet": {"webhook_events": event_id}},
                    upsert=True,
                )

                # If already verified via browser checkout, nothing more to do
                if existing and existing.get("status") == "verified":
                    return {"status": "success", "note": "already_verified"}

            # If not yet verified by browser, activate now
            now = datetime.now(timezone.utc)
            new_expiry = add_calendar_month(now)

            if db is not None:
                await db[COLLECTION_PAYMENT_RECORDS].update_one(
                    {"provider_order_id": order_id},
                    {
                        "$set": {
                            "provider_payment_id": payment_id,
                            "status": "verified",
                            "verified_at": now,
                        }
                    },
                    upsert=True,
                )
                new_sub = SubscriptionRecord(
                    plan_id=settings.SUBSCRIPTION_PLAN_ID,
                    plan_name=settings.SUBSCRIPTION_PLAN_NAME,
                    status="active",
                    amount_paise=settings.SUBSCRIPTION_AMOUNT_PAISE,
                    currency=settings.PAYMENT_CURRENCY,
                    billing_interval=settings.SUBSCRIPTION_BILLING_INTERVAL,
                    current_period_start=now,
                    current_period_end=new_expiry,
                    expires_at=new_expiry,
                    last_payment_id=payment_id,
                    created_at=now,
                    updated_at=now,
                )
                await db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one(
                    new_sub.model_dump(by_alias=False, exclude={"id"})
                )

            return {"status": "success", "activated": True}

        elif event_name == "payment.failed":
            payload_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payload_entity.get("order_id")
            error_desc = payload_entity.get("error_description", "Payment failed")
            if db is not None and order_id:
                await db[COLLECTION_PAYMENT_RECORDS].update_one(
                    {"provider_order_id": order_id},
                    {
                        "$set": {
                            "status": "failed",
                            "failure_reason": error_desc,
                            "updated_at": datetime.now(timezone.utc),
                        },
                        "$addToSet": {"webhook_events": event_id},
                    },
                )
            return {"status": "recorded_failure"}

        elif event_name in ("payment.refunded", "refund.processed"):
            payload_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payload_entity.get("order_id")
            payment_id = payload_entity.get("id")
            if db is not None and (order_id or payment_id):
                now = datetime.now(timezone.utc)
                match_filter = {"provider_order_id": order_id} if order_id else {"provider_payment_id": payment_id}
                await db[COLLECTION_PAYMENT_RECORDS].update_one(
                    match_filter,
                    {
                        "$set": {
                            "status": "refunded",
                            "updated_at": now,
                        },
                        "$addToSet": {"webhook_events": event_id},
                    },
                )
                # If this payment was used to activate the current subscription, expire it
                await db[COLLECTION_SUBSCRIPTION_RECORDS].update_many(
                    {"last_payment_id": payment_id, "status": "active"},
                    {"$set": {"status": "expired", "updated_at": now}},
                )
                logger.info(f"Processed refund webhook for payment {payment_id} (Order: {order_id}). Associated active subscription marked expired.")
            return {"status": "recorded_refund"}

        return {"status": "ignored"}

    @classmethod
    async def get_payment_history(
        cls, db: Optional[AsyncIOMotorDatabase], limit: int = 50
    ) -> PaymentHistoryResponse:
        """Retrieve audit log of payments for the authenticated administrator."""
        if db is None:
            return PaymentHistoryResponse(payments=[], total=0)

        cursor = db[COLLECTION_PAYMENT_RECORDS].find({}).sort("created_at", -1).limit(limit)
        items = []
        async for doc in cursor:
            amount_paise = doc.get("amount_paise", settings.SUBSCRIPTION_AMOUNT_PAISE)
            currency = doc.get("currency", "INR")
            items.append(
                PaymentHistoryItem(
                    payment_id=doc["payment_id"],
                    amount_paise=amount_paise,
                    amount_display=cls.format_amount_display(amount_paise, currency),
                    currency=currency,
                    status=doc.get("status", "created"),
                    provider_order_id=doc.get("provider_order_id", ""),
                    provider_payment_id=doc.get("provider_payment_id"),
                    created_at=doc.get("created_at", datetime.now(timezone.utc)),
                    verified_at=doc.get("verified_at"),
                )
            )

        return PaymentHistoryResponse(payments=items, total=len(items))


subscription_service = SubscriptionService()
