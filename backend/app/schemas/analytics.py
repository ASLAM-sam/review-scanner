"""
Analytics API Schemas
Defines schemas for the 4 core business metrics:
1. Total QR scans
2. Feedback submissions
3. Google review link clicks
4. Monthly activity
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyticsSummary(BaseModel):
    total_scans: int = Field(..., description="Unique human customer QR scans (deduplicated)")
    total_feedback_submissions: int = Field(..., description="Total successfully persisted feedback submissions")
    total_review_link_clicks: int = Field(..., description="Total intentional clicks to Google Review link")
    raw_scans: int = Field(default=0, description="Total raw scan events including refreshes and bots")


class MonthlyActivityItem(BaseModel):
    month: str = Field(..., description="Month in YYYY-MM format")
    scans: int = Field(default=0, description="Deduplicated customer QR scans")
    feedbacks: int = Field(default=0, description="Direct customer feedback submissions")
    review_clicks: int = Field(default=0, description="Google Review link clicks")


class MonthlyActivityData(BaseModel):
    period: str = Field(default="last_12_months", description="Activity period window")
    timezone: str = Field(default="Asia/Kolkata", description="Restaurant IANA timezone used for month grouping")
    months: List[MonthlyActivityItem] = Field(default_factory=list, description="Chronological 12-month activity timeline")


class DashboardAnalyticsResponse(BaseModel):
    summary: AnalyticsSummary
    monthly_activity: MonthlyActivityData
    generated_at: datetime = Field(default_factory=lambda: datetime.now())


# Maintained for backward compatibility with previous overview endpoints & existing components
class AnalyticsOverviewResponse(BaseModel):
    total_qr_scans: int = Field(..., description="Unique human customer QR scans (deduplicated)")
    total_feedback_submissions: int = Field(..., description="Total direct customer feedback forms submitted")
    google_review_link_clicks: int = Field(..., description="Total intentional clicks to Google Review page")
    monthly_activity: List[MonthlyActivityItem] = Field(..., description="Monthly breakdown of engagement")
    raw_qr_scans: int = Field(default=0, description="Total raw scan events including browser refreshes and bots")
