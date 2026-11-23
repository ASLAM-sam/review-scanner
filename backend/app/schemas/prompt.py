"""
Feedback Prompt API Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FeedbackPromptResponse(BaseModel):
    id: str
    category: str
    category_name: str
    text: str
    language: str
    sentiment: str  # positive, neutral, improvement
    is_active: bool = True


class PromptCategoryInfo(BaseModel):
    key: str
    name: str
    count: int


class PromptStatsResponse(BaseModel):
    total_prompts: int
    languages: dict
    categories: List[PromptCategoryInfo]
    sentiments: dict

