"""
Google Review Link Click Event Document Model
Recorded when customer chooses to open the official Google Review page.
NOTE: This is NOT a guarantee of a posted review, per Google policy.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ReviewLinkClickEvent(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str = Field(..., description="Anonymous session identifier")
    target_url: str = Field(..., description="Google review URL destination clicked")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

