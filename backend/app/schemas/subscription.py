"""
Subscription and Payment Schemas
Pydantic schemas for API request and response validation.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SubscriptionStatusResponse(BaseModel):
    status: str = Field(..., description="'active', 'expired', 'inactive', 'pending', 'cancelled'")
    plan_id: str
    plan_name: str
    amount_paise: int
    amount_display: str
    currency: str
    billing_interval: str
    started_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    expires_at: datetime
    remaining_days: int
    is_expired: bool
    can_renew: bool


class CreateOrderRequest(BaseModel):
    idempotency_key: Optional[str] = Field(default=None, max_length=100)


class CreateOrderResponse(BaseModel):
    order_id: str
    amount_paise: int
    currency: str
    key_id: str
    restaurant_name: str
    plan_name: str
    payment_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str = Field(..., min_length=5, max_length=100)
    razorpay_payment_id: str = Field(..., min_length=5, max_length=100)
    razorpay_signature: str = Field(..., min_length=10, max_length=256)


class VerifyPaymentResponse(BaseModel):
    success: bool
    status: str
    subscription_status: str
    expires_at: datetime
    message: str


class PaymentHistoryItem(BaseModel):
    payment_id: str
    amount_paise: int
    amount_display: str
    currency: str
    status: str
    provider_order_id: str
    provider_payment_id: Optional[str] = None
    created_at: datetime
    verified_at: Optional[datetime] = None


class PaymentHistoryResponse(BaseModel):
    payments: List[PaymentHistoryItem]
    total: int

