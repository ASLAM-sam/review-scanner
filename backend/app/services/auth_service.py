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
        """Seed default admin user in DB and remove all legacy email/password records."""
        if db is None:
            return None

        # Clean up any legacy admin accounts (e.g. old email-based or non-aslam accounts)
        # to ensure previous email and password data is completely wiped out as requested
        await db[COLLECTION_ADMIN_USERS].delete_many({"username": {"$ne": settings.INITIAL_ADMIN_USERNAME}})
        await db[COLLECTION_ADMIN_USERS].delete_many({"username": {"$exists": False}})

        existing = await db[COLLECTION_ADMIN_USERS].find_one({"username": settings.INITIAL_ADMIN_USERNAME})
        hashed_pw = get_password_hash(settings.INITIAL_ADMIN_PASSWORD)

        if existing:
            # Update password to ensure it matches the requested INITIAL_ADMIN_PASSWORD
            await db[COLLECTION_ADMIN_USERS].update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "hashed_password": hashed_pw,
                        "updated_at": datetime.now(timezone.utc),
                        "is_active": True,
                    }
                },
            )
            existing["_id"] = str(existing["_id"])
            return AdminUserInDB(**existing)

        admin = AdminUserInDB(
            username=settings.INITIAL_ADMIN_USERNAME,
            hashed_password=hashed_pw,
            full_name=f"{settings.RESTAURANT_NAME} Admin",
            is_active=True,
        )
        doc = admin.model_dump(by_alias=False, exclude={"id"})
        result = await db[COLLECTION_ADMIN_USERS].insert_one(doc)
        logger.info(f"Initialized default admin account: {settings.INITIAL_ADMIN_USERNAME}")
        doc["_id"] = str(result.inserted_id)
        return AdminUserInDB(**doc)

    @classmethod
    async def get_by_username(cls, db: Optional[AsyncIOMotorDatabase], username: str) -> Optional[AdminUserInDB]:
        if db is None:
            if username.lower() == settings.INITIAL_ADMIN_USERNAME.lower():
                return AdminUserInDB(
                    id="mock-admin-id",
                    username=settings.INITIAL_ADMIN_USERNAME,
                    hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                    full_name=f"{settings.RESTAURANT_NAME} Admin",
                    is_active=True,
                )
            return None

        doc = await db[COLLECTION_ADMIN_USERS].find_one({"username": username.lower()})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return AdminUserInDB(**doc)

    @classmethod
    async def get_by_id(cls, db: Optional[AsyncIOMotorDatabase], user_id: str) -> Optional[AdminUserInDB]:
        if db is None:
            return AdminUserInDB(
                id="mock-admin-id",
                username=settings.INITIAL_ADMIN_USERNAME,
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
        username: str,
        password: str,
    ) -> Optional[AdminUserInDB]:
        """Verify admin credentials."""
        user = await cls.get_by_username(db, username)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


auth_service = AuthService()
