"""
FastAPI Dependencies Module
Provides database access and authenticated user injection.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.mongodb import get_database
from app.models.user import AdminUserInDB
from app.services.auth_service import auth_service

from app.services.restaurant_service import restaurant_service

security_bearer = HTTPBearer(auto_error=False)


async def get_db() -> Optional[AsyncIOMotorDatabase]:
    """Dependency returning active MongoDB database instance (lazy-connected for serverless)."""
    db = get_database()
    if db is None:
        await connect_to_mongo()
        db = get_database()
        if db is not None:
            await restaurant_service.ensure_initial_settings(db)
            await auth_service.ensure_initial_admin(db)
    return db


async def get_current_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
) -> AdminUserInDB:
    """
    Dependency validating JWT from either Authorization header (Bearer token)
    or secure HttpOnly session cookie ('admin_access_token').
    """
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Check Bearer token from header first
    raw_token: Optional[str] = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    # 2. Fall back to secure HttpOnly cookie
    elif "admin_access_token" in request.cookies:
        raw_token = request.cookies.get("admin_access_token")

    if not raw_token:
        raise unauthorized_exc

    try:
        payload = jwt.decode(
            raw_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "iat"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise unauthorized_exc

    user_email = payload.get("sub")
    if not user_email:
        raise unauthorized_exc

    user = await auth_service.get_by_email(db, user_email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
