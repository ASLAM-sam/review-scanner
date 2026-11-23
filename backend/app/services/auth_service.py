"""
Admin Authentication Service
Manages initial admin seeding, credential verification, and user lookup.
"""

from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_password_hash, verify_password
from app.db.collections import COLLECTION_ADMIN_USERS
from app.models.user import AdminUserInDB


class AuthService:
    @classmethod
    async def ensure_initial_admin(cls, db: Optional[AsyncIOMotorDatabase]) -> Optional[AdminUserInDB]:
        """Seed default admin user in DB if none exists."""
        if db is None:
            return None

        count = await db[COLLECTION_ADMIN_USERS].count_documents({})
        if count > 0:
            return None

        hashed_pw = get_password_hash(settings.INITIAL_ADMIN_PASSWORD)
        admin = AdminUserInDB(
            email=settings.INITIAL_ADMIN_EMAIL,
            hashed_password=hashed_pw,
            full_name=f"{settings.RESTAURANT_NAME} Admin",
            is_active=True,
        )
        doc = admin.model_dump(by_alias=False, exclude={"id"})
        result = await db[COLLECTION_ADMIN_USERS].insert_one(doc)
        logger.info(f"Initialized default admin account: {settings.INITIAL_ADMIN_EMAIL}")
        doc["_id"] = str(result.inserted_id)
        return AdminUserInDB(**doc)

    @classmethod
    async def get_by_email(cls, db: Optional[AsyncIOMotorDatabase], email: str) -> Optional[AdminUserInDB]:
        if db is None:
            if email.lower() == settings.INITIAL_ADMIN_EMAIL.lower():
                return AdminUserInDB(
                    id="mock-admin-id",
                    email=settings.INITIAL_ADMIN_EMAIL,
                    hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                    full_name=f"{settings.RESTAURANT_NAME} Admin",
                    is_active=True,
                )
            return None

        doc = await db[COLLECTION_ADMIN_USERS].find_one({"email": email.lower()})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return AdminUserInDB(**doc)

    @classmethod
    async def get_by_id(cls, db: Optional[AsyncIOMotorDatabase], user_id: str) -> Optional[AdminUserInDB]:
        if db is None:
            return AdminUserInDB(
                id="mock-admin-id",
                email=settings.INITIAL_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                full_name=f"{settings.RESTAURANT_NAME} Admin",
                is_active=True,
            )

        try:
            doc = await db[COLLECTION_ADMIN_USERS].find_one({"_id": ObjectId(user_id)})
            if not doc:
                return None
            doc["_id"] = str(doc["_id"])
            return AdminUserInDB(**doc)
        except Exception:
            return None

    @classmethod
    async def authenticate(
        cls,
        db: Optional[AsyncIOMotorDatabase],
        email: str,
        password: str,
    ) -> Optional[AdminUserInDB]:
        """Verify admin credentials."""
        user = await cls.get_by_email(db, email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


auth_service = AuthService()
