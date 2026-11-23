"""API schemas."""
from app.schemas.common import APIResponse, MessageResponse
from app.schemas.auth import LoginRequest, TokenResponse, AdminUserResponse
from app.schemas.restaurant import (
    RestaurantPublicResponse,
    RestaurantAdminResponse,
    RestaurantUpdateRequest,
)
from app.schemas.qr import QRScanRequest, QRScanResponse, QRDetailsResponse
from app.schemas.feedback import (
    FeedbackCreateRequest,
    FeedbackResponse,
    ReviewClickRequest,
)
from app.schemas.analytics import MonthlyActivityItem, AnalyticsOverviewResponse

__all__ = [
    "APIResponse",
    "MessageResponse",
    "LoginRequest",
    "TokenResponse",
    "AdminUserResponse",
    "RestaurantPublicResponse",
    "RestaurantAdminResponse",
    "RestaurantUpdateRequest",
    "QRScanRequest",
    "QRScanResponse",
    "QRDetailsResponse",
    "FeedbackCreateRequest",
    "FeedbackResponse",
    "ReviewClickRequest",
    "MonthlyActivityItem",
    "AnalyticsOverviewResponse",
]

