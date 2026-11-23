"""
Subscription Record Document Model
Single-Tenant Independent Restaurant Deployment
"""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class SubscriptionRecord(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    plan_id: str = Field(default="plan_standard_monthly", max_length=50)
    plan_name: str = Field(default="Standard Monthly", max_length=100)
    status: str = Field(
        default="active",
        description="'inactive', 'pending', 'active', 'expired', 'payment_failed', 'cancelled'",
    )
    amount_paise: int = Field(default=24900, description="Amount in integer paise (e.g. 24900 = ₹249)")
    currency: str = Field(default="INR", max_length=10)
    billing_interval: str = Field(default="monthly", max_length=20)
    started_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_payment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
