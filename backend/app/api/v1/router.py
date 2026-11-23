"""
API v1 Router Aggregator
Mounts public, auth, admin, and analytics routes under /api/v1.
"""

from fastapi import APIRouter
from app.api.v1.public import router as public_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.webhook import router as webhook_router

api_v1_router = APIRouter()
api_v1_router.include_router(public_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(webhook_router)

