"""
QR Code API Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class QRScanRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Optional client-generated or previous session ID")
    referrer: Optional[str] = Field(default=None, max_length=500)


class QRScanResponse(BaseModel):
    session_id: str
    destination_url: str
    subscription_status: str = "active"  # "active" or "expired"
    restaurant_name: str
    restaurant_slug: str


class QRDetailsResponse(BaseModel):
    slug: str
    destination_url: str
    qr_svg: str
    qr_data_url: str

