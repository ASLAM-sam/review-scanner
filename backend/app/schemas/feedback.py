"""
Feedback Submission API Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    food_rating: int = Field(..., ge=1, le=5)
    service_rating: int = Field(..., ge=1, le=5)
    ambience_rating: int = Field(..., ge=1, le=5)
    overall_experience: str = Field(..., pattern="^(positive|neutral|negative)$")
    positive_tags: List[str] = Field(default_factory=list, max_length=20)
    improvement_tags: List[str] = Field(default_factory=list, max_length=20)
    selected_prompts: List[str] = Field(default_factory=list, max_length=20)
    customer_notes: Optional[str] = Field(default="", max_length=1000)


class FeedbackResponse(BaseModel):
    id: Optional[str] = None
    session_id: str
    overall_experience: str
    created_at: datetime
    google_review_prompt_eligible: bool = True  # Customer is always given the option, never gated


class ReviewClickRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    target_url: Optional[str] = Field(default=None, max_length=1000)

