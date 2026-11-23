"""
Restaurant Analytics Service
Computes strictly the four agreed business metrics:
1. Total QR scans (verified human customer scans)
2. Total feedback submissions (persisted forms)
3. Google review link clicks (intentional clicks to Google Review URL)
4. Monthly activity (chronological 12-month timeline respecting restaurant timezone)
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import zoneinfo
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import logger
from app.db.collections import (
    COLLECTION_FEEDBACK_SUBMISSIONS,
    COLLECTION_QR_SCANS,
    COLLECTION_REVIEW_LINK_CLICKS,
)
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsSummary,
    DashboardAnalyticsResponse,
    MonthlyActivityData,
    MonthlyActivityItem,
)


def get_rolling_12_months(target_tz_str: str) -> Tuple[List[str], datetime, zoneinfo.ZoneInfo]:
    """
    Generate chronological 12 calendar months (ending with current month) in target timezone.
    Returns:
    1. List of 12 strings in YYYY-MM format: ['2025-12', ..., '2026-11']
    2. UTC datetime representing the start (00:00:00) of the earliest month in local time.
    3. The resolved ZoneInfo instance.
    """
    try:
        tz = zoneinfo.ZoneInfo(target_tz_str)
    except Exception:
        logger.warning(f"Invalid timezone '{target_tz_str}'. Falling back to 'Asia/Kolkata'.")
        tz = zoneinfo.ZoneInfo("Asia/Kolkata")
        target_tz_str = "Asia/Kolkata"

    now_local = datetime.now(tz)
    cur_year = now_local.year
    cur_month = now_local.month

    # Generate 12 months in chronological order
    months: List[str] = []
    for i in range(11, -1, -1):
        m = cur_month - i
        y = cur_year
        while m <= 0:
            m += 12
            y -= 1
        months.append(f"{y:04d}-{m:02d}")

    # Earliest month start in target timezone converted to UTC for DB matching
    earliest_y, earliest_m = int(months[0][:4]), int(months[0][5:7])
    start_local = datetime(earliest_y, earliest_m, 1, 0, 0, 0, tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc)

    return months, start_utc, tz


class AnalyticsService:
    @classmethod
    async def get_dashboard_analytics(
        cls,
        db: Optional[AsyncIOMotorDatabase],
        tz_override: Optional[str] = None,
    ) -> DashboardAnalyticsResponse:
        """
        Compute authoritative dashboard analytics for the single-tenant restaurant.
        Respects restaurant timezone, bot filtering, duplicate prevention, and zero-activity months.
        """
        target_tz_str = tz_override or settings.RESTAURANT_TIMEZONE
        twelve_months, start_utc, tz = get_rolling_12_months(target_tz_str)

        if db is None:
            # Fallback for offline or unseeded database
            return DashboardAnalyticsResponse(
                summary=AnalyticsSummary(
                    total_scans=0,
                    total_feedback_submissions=0,
                    total_review_link_clicks=0,
                    raw_scans=0,
                ),
                monthly_activity=MonthlyActivityData(
                    period="last_12_months",
                    timezone=target_tz_str,
                    months=[
                        MonthlyActivityItem(month=m, scans=0, feedbacks=0, review_clicks=0)
                        for m in twelve_months
                    ],
                ),
                generated_at=datetime.now(timezone.utc),
            )

        try:
            # 1. Total Summary Counts:
            # Metric 1: Total QR Scans (verified human scans, is_bot!=True)
            unique_scans_query = {
                "is_bot": {"$ne": True},
                "$or": [{"is_unique": True}, {"is_unique": {"$exists": False}}],
            }
            total_unique_scans = await db[COLLECTION_QR_SCANS].count_documents(unique_scans_query)
            total_raw_scans = await db[COLLECTION_QR_SCANS].count_documents({})

            # Metric 2: Total Feedback Submissions (persisted records only)
            total_feedbacks = await db[COLLECTION_FEEDBACK_SUBMISSIONS].count_documents({})

            # Metric 3: Total Google Review Link Clicks (tracked clicks only)
            total_clicks = await db[COLLECTION_REVIEW_LINK_CLICKS].count_documents({})

            # 2. Monthly Activity Aggregation:
            monthly_data: Dict[str, Dict[str, int]] = {
                m: {"scans": 0, "feedbacks": 0, "review_clicks": 0} for m in twelve_months
            }

            # A. Aggregate QR Scans (filtered by bot and 12-month start boundary)
            scans_match = {
                "is_bot": {"$ne": True},
                "created_at": {"$gte": start_utc},
            }
            await cls._aggregate_collection(
                db=db,
                collection_name=COLLECTION_QR_SCANS,
                match_filter=scans_match,
                target_tz_str=target_tz_str,
                tz=tz,
                monthly_dict=monthly_data,
                metric_key="scans",
            )

            # B. Aggregate Feedback Submissions
            feedbacks_match = {"created_at": {"$gte": start_utc}}
            await cls._aggregate_collection(
                db=db,
                collection_name=COLLECTION_FEEDBACK_SUBMISSIONS,
                match_filter=feedbacks_match,
                target_tz_str=target_tz_str,
                tz=tz,
                monthly_dict=monthly_data,
                metric_key="feedbacks",
            )

            # C. Aggregate Review Link Clicks
            clicks_match = {"created_at": {"$gte": start_utc}}
            await cls._aggregate_collection(
                db=db,
                collection_name=COLLECTION_REVIEW_LINK_CLICKS,
                match_filter=clicks_match,
                target_tz_str=target_tz_str,
                tz=tz,
                monthly_dict=monthly_data,
                metric_key="review_clicks",
            )

            # Assemble chronological 12-month items
            monthly_list = [
                MonthlyActivityItem(
                    month=m,
                    scans=monthly_data[m]["scans"],
                    feedbacks=monthly_data[m]["feedbacks"],
                    review_clicks=monthly_data[m]["review_clicks"],
                )
                for m in twelve_months
            ]

            return DashboardAnalyticsResponse(
                summary=AnalyticsSummary(
                    total_scans=total_unique_scans,
                    total_feedback_submissions=total_feedbacks,
                    total_review_link_clicks=total_clicks,
                    raw_scans=total_raw_scans,
                ),
                monthly_activity=MonthlyActivityData(
                    period="last_12_months",
                    timezone=target_tz_str,
                    months=monthly_list,
                ),
                generated_at=datetime.now(timezone.utc),
            )

        except Exception as exc:
            logger.error(f"Error computing dashboard analytics: {exc}")
            return DashboardAnalyticsResponse(
                summary=AnalyticsSummary(
                    total_scans=0,
                    total_feedback_submissions=0,
                    total_review_link_clicks=0,
                    raw_scans=0,
                ),
                monthly_activity=MonthlyActivityData(
                    period="last_12_months",
                    timezone=target_tz_str,
                    months=[
                        MonthlyActivityItem(month=m, scans=0, feedbacks=0, review_clicks=0)
                        for m in twelve_months
                    ],
                ),
                generated_at=datetime.now(timezone.utc),
            )

    @classmethod
    async def _aggregate_collection(
        cls,
        db: AsyncIOMotorDatabase,
        collection_name: str,
        match_filter: dict,
        target_tz_str: str,
        tz: zoneinfo.ZoneInfo,
        monthly_dict: Dict[str, Dict[str, int]],
        metric_key: str,
    ) -> None:
        """
        Aggregate counts by month.
        Attempts native MongoDB $dateToString with timezone parameter.
        Falls back to projection if mock database does not implement $dateToString.
        """
        try:
            pipeline = [
                {"$match": match_filter},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m",
                                "date": "$created_at",
                                "timezone": target_tz_str,
                            }
                        },
                        "count": {"$sum": 1},
                    }
                },
            ]
            async for doc in db[collection_name].aggregate(pipeline):
                month_key = doc.get("_id")
                if month_key and month_key in monthly_dict:
                    monthly_dict[month_key][metric_key] = doc["count"]
        except Exception:
            # Fallback for mock test engines (e.g. mongomock) that do not support $dateToString
            cursor = db[collection_name].find(match_filter, {"created_at": 1, "_id": 0})
            async for doc in cursor:
                dt = doc.get("created_at")
                if dt:
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    local_dt = dt.astimezone(tz)
                    m_key = local_dt.strftime("%Y-%m")
                    if m_key in monthly_dict:
                        monthly_dict[m_key][metric_key] += 1

    @classmethod
    async def get_overview(
        cls,
        db: Optional[AsyncIOMotorDatabase],
    ) -> AnalyticsOverviewResponse:
        """Backward-compatible method returning legacy overview response."""
        dash = await cls.get_dashboard_analytics(db)
        return AnalyticsOverviewResponse(
            total_qr_scans=dash.summary.total_scans,
            total_feedback_submissions=dash.summary.total_feedback_submissions,
            google_review_link_clicks=dash.summary.total_review_link_clicks,
            monthly_activity=dash.monthly_activity.months,
            raw_qr_scans=dash.summary.raw_scans,
        )


analytics_service = AnalyticsService()
