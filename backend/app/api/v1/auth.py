"""
Authentication Endpoints
Handles admin login and token verification.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_admin, get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import AdminUserInDB
from app.schemas.auth import AdminUserResponse, LoginRequest, TokenResponse
from app.schemas.common import APIResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Admin Authentication"])


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login_admin(
    payload: LoginRequest,
    response: Response,
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Authenticate administrator, return signed JWT token, and set secure HttpOnly session cookie.
    Dual protection: browser uses HttpOnly cookie (XSS defense), API clients can use Bearer header.
    """
    user = await auth_service.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.email})
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Set secure HttpOnly session cookie
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="admin_access_token",
        value=token,
        max_age=expires_in_seconds,
        httponly=True,
        secure=is_prod,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )

    return APIResponse(
        success=True,
        message="Login successful",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in_seconds,
        ),
    )


@router.post("/logout", response_model=APIResponse[dict])
async def logout_admin(
    response: Response,
):
    """Clear administrator authentication session cookie."""
    response.delete_cookie(
        key="admin_access_token",
        path="/",
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )
    return APIResponse(
        success=True,
        message="Logged out successfully",
        data={"authenticated": False},
    )


@router.get("/me", response_model=APIResponse[AdminUserResponse])
async def get_current_admin_user(
    current_admin: AdminUserInDB = Depends(get_current_admin),
):
    """Get the currently logged-in administrator's profile."""
    return APIResponse(
        success=True,
        message="Current user profile retrieved",
        data=AdminUserResponse(
            id=current_admin.id,
            email=current_admin.email,
            full_name=current_admin.full_name,
            is_active=current_admin.is_active,
        ),
    )

