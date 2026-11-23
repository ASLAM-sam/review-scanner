"""
Customer Feedback Submission Document Model
Captures food, service, ambience ratings and voluntary remarks.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class FeedbackSubmission(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str = Field(..., description="Anonymous session identifier linked to the scan")
    food_rating: int = Field(..., ge=1, le=5, description="1 to 5 rating for food quality")
    service_rating: int = Field(..., ge=1, le=5, description="1 to 5 rating for service")
    ambience_rating: int = Field(..., ge=1, le=5, description="1 to 5 rating for ambience")
    overall_experience: str = Field(..., description="'positive', 'neutral', or 'negative'")
    positive_tags: List[str] = Field(default_factory=list, description="Selected positive tags")
    improvement_tags: List[str] = Field(default_factory=list, description="Selected improvement tags")
    selected_prompts: List[str] = Field(default_factory=list, description="Selected smart feedback prompt texts or IDs")
    customer_notes: Optional[str] = Field(default="", max_length=1000, description="Optional text feedback")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

