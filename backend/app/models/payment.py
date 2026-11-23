"""
Payment Record Document Model
Maintains audit trail of all transaction attempts, verifications, and webhooks.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class PaymentRecord(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    payment_id: str = Field(..., description="Internal payment tracking identifier")
    subscription_id: Optional[str] = None
    payment_provider: str = Field(default="razorpay", max_length=50)
    provider_order_id: str = Field(..., description="Provider order ID (e.g. order_xxx)")
    provider_payment_id: Optional[str] = Field(default=None, description="Provider payment ID (e.g. pay_xxx)")
    provider_signature: Optional[str] = Field(default=None, description="Cryptographic verification signature")
    amount_paise: int = Field(..., description="Integer paise, e.g. 24900")
    currency: str = Field(default="INR", max_length=10)
    status: str = Field(
        default="created",
        description="'created', 'pending', 'verified', 'failed', 'cancelled'",
    )
    failure_reason: Optional[str] = None
    idempotency_key: Optional[str] = None
    webhook_events: List[str] = Field(default_factory=list, description="IDs of processed webhook deliveries")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def convert_id(cls, v: Any) -> Optional[str]:
        if v is not None:
            return str(v)
        return None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
