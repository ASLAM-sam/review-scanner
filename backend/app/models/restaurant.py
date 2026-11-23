"""
Restaurant Settings Document Model
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class RestaurantSettingsInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=120)
    slug: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default="", max_length=500)
    logo_url: Optional[str] = Field(default="", max_length=1000)
    primary_color: str = Field(default="#16a34a", max_length=30)
    secondary_color: str = Field(default="#15803d", max_length=30)
    google_review_url: str = Field(..., max_length=1000)
    qr_destination_url: str = Field(..., max_length=1000)
    contact_phone: Optional[str] = Field(default="", max_length=50)
    contact_email: Optional[str] = Field(default="", max_length=120)
    address: Optional[str] = Field(default="", max_length=300)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

