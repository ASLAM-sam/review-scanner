"""
QR Scan Event Document Model
Recorded whenever a customer scans the physical QR code.
Distinguishes unique human visits from refreshes, duplicates, and automated web crawlers.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class QRScanEvent(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str = Field(..., description="Unique anonymous session ID for this scan flow")
    ip_hash: Optional[str] = Field(default=None, description="One-way salted hash of IP to prevent PII storage")
    user_agent: Optional[str] = Field(default=None, max_length=500)
    referrer: Optional[str] = Field(default=None, max_length=500)
    is_unique: bool = Field(default=True, description="True if initial human visit, False if refresh/reload")
    is_bot: bool = Field(default=False, description="True if automated crawler / preview bot detected")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
