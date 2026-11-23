"""
Restaurant Settings Service
Manages restaurant branding, configuration, and defaults.
"""

from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import logger
from app.db.collections import COLLECTION_RESTAURANT_SETTINGS
from app.models.restaurant import RestaurantSettingsInDB
from app.schemas.restaurant import RestaurantUpdateRequest


class RestaurantService:
    @staticmethod
    def get_fallback_settings() -> RestaurantSettingsInDB:
        """Construct settings object from environment variables."""
        return RestaurantSettingsInDB(
            name=settings.RESTAURANT_NAME,
            slug=settings.RESTAURANT_SLUG,
            description=settings.RESTAURANT_DESCRIPTION,
            logo_url=settings.RESTAURANT_LOGO_URL,
            primary_color=settings.RESTAURANT_PRIMARY_COLOR,
            secondary_color=settings.RESTAURANT_SECONDARY_COLOR,
            google_review_url=settings.RESTAURANT_GOOGLE_REVIEW_URL,
            qr_destination_url=f"{settings.RESTAURANT_QR_BASE_URL.rstrip('/')}/{settings.RESTAURANT_SLUG}",
            contact_phone=settings.RESTAURANT_CONTACT_PHONE,
            contact_email=settings.RESTAURANT_CONTACT_EMAIL,
            address=settings.RESTAURANT_ADDRESS,
            is_active=True,
        )

    @classmethod
    async def ensure_initial_settings(cls, db: Optional[AsyncIOMotorDatabase]) -> RestaurantSettingsInDB:
        """Seed initial configuration in database if missing."""
        if db is None:
            return cls.get_fallback_settings()

        existing = await db[COLLECTION_RESTAURANT_SETTINGS].find_one({"slug": settings.RESTAURANT_SLUG})
        if existing:
            existing["_id"] = str(existing["_id"])
            return RestaurantSettingsInDB(**existing)

        # Seed new installation settings
        fallback = cls.get_fallback_settings()
        doc = fallback.model_dump(by_alias=False, exclude={"id"})
        result = await db[COLLECTION_RESTAURANT_SETTINGS].insert_one(doc)
        logger.info(f"Initialized restaurant settings for '{settings.RESTAURANT_NAME}' with ID {result.inserted_id}")
        doc["_id"] = str(result.inserted_id)
        return RestaurantSettingsInDB(**doc)

    @classmethod
    async def get_settings(cls, db: Optional[AsyncIOMotorDatabase]) -> RestaurantSettingsInDB:
        """Fetch current restaurant settings."""
        if db is None:
            return cls.get_fallback_settings()

        doc = await db[COLLECTION_RESTAURANT_SETTINGS].find_one({"is_active": True})
        if not doc:
            return await cls.ensure_initial_settings(db)

        doc["_id"] = str(doc["_id"])
        return RestaurantSettingsInDB(**doc)

    @classmethod
    async def update_settings(
        cls,
        db: Optional[AsyncIOMotorDatabase],
        update_data: RestaurantUpdateRequest,
    ) -> RestaurantSettingsInDB:
        """Update existing restaurant settings with validated fields."""
        current = await cls.get_settings(db)
        if db is None:
            return current

        update_dict = {
            k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None
        }
        if not update_dict:
            return current

        update_dict["updated_at"] = datetime.now(timezone.utc)
        await db[COLLECTION_RESTAURANT_SETTINGS].update_one(
            {"slug": current.slug},
            {"$set": update_dict},
        )
        logger.info(f"Updated restaurant settings for '{current.slug}': {list(update_dict.keys())}")
        return await cls.get_settings(db)


restaurant_service = RestaurantService()

