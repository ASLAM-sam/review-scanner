"""
Admin User Document Model
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class AdminUserInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    username: str = Field(..., min_length=3, max_length=50)
    hashed_password: str
    email: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default="Restaurant Administrator", max_length=120)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

