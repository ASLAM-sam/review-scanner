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
        """Seed default admin users ('aslam' and 'admin') with configured password and purge legacy records."""
        if db is None:
            return None

        # Clean up any legacy admin accounts without username
        await db[COLLECTION_ADMIN_USERS].delete_many({"username": {"$exists": False}})

        # Allow both 'aslam' and 'admin' with the password
        allowed_users = list(set(["aslam", "admin", settings.INITIAL_ADMIN_USERNAME.lower()]))
        # Remove any other accounts
        await db[COLLECTION_ADMIN_USERS].delete_many({"username": {"$nin": allowed_users}})

        hashed_pw = get_password_hash(settings.INITIAL_ADMIN_PASSWORD)
        first_admin = None

        for uname in allowed_users:
            existing = await db[COLLECTION_ADMIN_USERS].find_one({"username": uname})
            if existing:
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
                if not first_admin:
                    first_admin = AdminUserInDB(**existing)
            else:
                admin_obj = AdminUserInDB(
                    username=uname,
                    hashed_password=hashed_pw,
                    full_name=f"{uname.capitalize()} (Administrator)",
                    is_active=True,
                )
                doc = admin_obj.model_dump(by_alias=False, exclude={"id"})
                result = await db[COLLECTION_ADMIN_USERS].insert_one(doc)
                doc["_id"] = str(result.inserted_id)
                if not first_admin:
                    first_admin = AdminUserInDB(**doc)

        logger.info(f"Verified admin accounts ({', '.join(allowed_users)}) with configured password")
        return first_admin

    @classmethod
    async def get_by_username(cls, db: Optional[AsyncIOMotorDatabase], username: str) -> Optional[AdminUserInDB]:
        normalized = username.strip().lower()
        if db is None:
            if normalized in ("aslam", "admin", settings.INITIAL_ADMIN_USERNAME.lower()):
                return AdminUserInDB(
                    id="mock-admin-id",
                    username=normalized,
                    hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                    full_name="Administrator",
                    is_active=True,
                )
            return None

        doc = await db[COLLECTION_ADMIN_USERS].find_one({"username": normalized})
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
