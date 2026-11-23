"""
Restaurant Analytics Endpoints
Protected routes: provides strictly the 4 business metrics for authenticated restaurant administrators:
1. Total QR Scans
2. Total Feedback Submissions
3. Google Review Link Clicks
4. Monthly Activity (12-month timeline)
"""

from typing import Optional
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_admin, get_db
from app.models.user import AdminUserInDB
from app.schemas.analytics import AnalyticsOverviewResponse, DashboardAnalyticsResponse
from app.schemas.common import APIResponse
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Restaurant Analytics"])


@router.get("/dashboard", response_model=APIResponse[DashboardAnalyticsResponse])
async def get_dashboard_analytics(
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Fetch authoritative restaurant dashboard metrics:
    - Summary counts (Scans, Feedbacks, Google Review Clicks)
    - 12-Month chronological activity timeline respecting restaurant timezone
    - Protected: requires active admin authentication.
    """
    dash_data = await analytics_service.get_dashboard_analytics(db)
    return APIResponse(
        success=True,
        message="Dashboard analytics loaded successfully",
        data=dash_data,
    )


@router.get("/overview", response_model=APIResponse[AnalyticsOverviewResponse])
async def get_analytics_overview(
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Backward-compatible overview endpoint.
    Maintained for legacy clients and test suites.
    """
    overview = await analytics_service.get_overview(db)
    return APIResponse(
        success=True,
        message="Analytics overview loaded",
        data=overview,
    )
