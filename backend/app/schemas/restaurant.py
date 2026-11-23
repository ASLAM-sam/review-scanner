"""
Restaurant Configuration API Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RestaurantPublicResponse(BaseModel):
    name: str
    slug: str
    description: Optional[str] = ""
    logo_url: Optional[str] = ""
    primary_color: str = "#16a34a"
    secondary_color: str = "#15803d"
    google_review_url: str
    contact_phone: Optional[str] = ""
    contact_email: Optional[str] = ""
    address: Optional[str] = ""
    is_active: bool = True
    subscription_status: str = "active"


class RestaurantAdminResponse(RestaurantPublicResponse):
    id: Optional[str] = None
    qr_destination_url: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RestaurantUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    logo_url: Optional[str] = Field(default=None, max_length=1000)
    primary_color: Optional[str] = Field(default=None, max_length=30)
    secondary_color: Optional[str] = Field(default=None, max_length=30)
    google_review_url: Optional[str] = Field(default=None, max_length=1000)
    qr_destination_url: Optional[str] = Field(default=None, max_length=1000)
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    contact_email: Optional[str] = Field(default=None, max_length=120)
    address: Optional[str] = Field(default=None, max_length=300)

