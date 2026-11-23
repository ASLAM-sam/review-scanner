"""
Payment Webhook Handler Module
Handles asynchronous payment notifications from Razorpay.
Publicly accessible endpoint protected by HMAC-SHA256 signature verification.
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db
from app.core.logging import logger
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/webhook", tags=["Payment Webhooks"])


@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Receive and process Razorpay Webhook events.
    Verifies raw body signature with RAZORPAY_WEBHOOK_SECRET.
    Guarantees idempotency and prevents double activation.
    """
    if not x_razorpay_signature:
        logger.warning("Webhook received without X-Razorpay-Signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook signature header",
        )

    # Read raw body bytes for cryptographic signature validation
    raw_body = await request.body()

    try:
        event_payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        logger.warning(f"Failed to parse webhook JSON body: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload in webhook body",
        )

    result = await subscription_service.process_webhook(
        db=db,
        raw_body=raw_body,
        signature=x_razorpay_signature,
        event_data=event_payload,
    )

    return {"status": "ok", "result": result}

