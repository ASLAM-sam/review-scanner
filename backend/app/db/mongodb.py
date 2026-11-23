"""
MongoDB Async Database Connection & Index Management
Uses Motor (async Python driver for MongoDB)
Single-Tenant Independent Deployment Architecture
"""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from pymongo.errors import PyMongoError, ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings
from app.core.logging import logger
from app.db.collections import (
    COLLECTION_RESTAURANT_SETTINGS,
    COLLECTION_ADMIN_USERS,
    COLLECTION_QR_SCANS,
    COLLECTION_FEEDBACK_SUBMISSIONS,
    COLLECTION_REVIEW_LINK_CLICKS,
    COLLECTION_SUBSCRIPTION_RECORDS,
    COLLECTION_PAYMENT_RECORDS,
)


class DatabaseClient:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_client = DatabaseClient()
_connect_lock = asyncio.Lock()


async def connect_to_mongo(
    uri: Optional[str] = None,
    db_name: Optional[str] = None,
    max_retries: int = 3,
    retry_delay_seconds: float = 1.5,
) -> bool:
    """
    Initialize MongoDB connection pool and verify connectivity with automatic retries.
    Handles startup timing races where MongoDB container is booting or serverless cold starts.
    """
    target_uri = uri or settings.MONGODB_URI
    target_db = db_name or settings.MONGODB_DB_NAME

    # If default connection is already active and no custom uri/db requested, reuse existing
    if uri is None and db_name is None and db_client.db is not None and db_client.client is not None:
        return True

    async with _connect_lock:
        if uri is None and db_name is None and db_client.db is not None and db_client.client is not None:
            return True

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"Connecting to MongoDB database '{target_db}' (Attempt {attempt}/{max_retries})..."
            )
            client = AsyncIOMotorClient(
                target_uri,
                serverSelectionTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
                connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
                maxPoolSize=20,
                minPoolSize=2,
                retryWrites=True,
            )
            db = client[target_db]

            # Verify connection with ping command
            await db.command("ping")
            
            db_client.client = client
            db_client.db = db
            logger.info(f"Successfully connected to MongoDB '{target_db}'.")

            # Initialize indexes and schema validations
            await init_db_indexes(db_client.db)
            return True

        except (ServerSelectionTimeoutError, ConnectionFailure, PyMongoError) as exc:
            logger.warning(
                f"Connection attempt {attempt}/{max_retries} to MongoDB at {target_uri} failed: {exc}"
            )
            if attempt < max_retries:
                await asyncio.sleep(retry_delay_seconds * attempt)
        except Exception as exc:
            logger.warning(f"Unexpected error connecting to MongoDB: {exc}")
            break

    if uri is None and settings.ENVIRONMENT in ("development", "test"):
        try:
            logger.info("Initializing high-fidelity in-memory MongoDB client for development/testing...")
            from mongomock_motor import AsyncMongoMockClient
            mock_client = AsyncMongoMockClient()
            db_client.client = mock_client
            db_client.db = mock_client[target_db]
            await init_db_indexes(db_client.db)
            return True
        except Exception as exc:
            logger.warning(f"Could not initialize in-memory fallback MongoDB: {exc}")

    logger.warning("Could not establish live MongoDB connection. Operating in fallback/in-memory test mode.")
    return False


async def close_mongo_connection() -> None:
    """Close MongoDB connection pool cleanly."""
    if db_client.client is not None:
        logger.info("Closing MongoDB connection pool...")
        db_client.client.close()
        db_client.client = None
        db_client.db = None
        logger.info("MongoDB connection pool closed.")


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Dependency / accessor for active MongoDB database instance."""
    return db_client.db


async def is_db_alive() -> bool:
    """Check whether the active MongoDB client can ping the server."""
    if db_client.db is None:
        return False
    try:
        await db_client.db.command("ping")
        return True
    except Exception:
        return False


async def init_db_indexes(db: AsyncIOMotorDatabase) -> None:
    """
    Establish required indexes across all 6 collections:
    1. restaurant_settings (unique slug)
    2. admin_users (unique email)
    3. qr_scans (created_at, session_id, ip_hash)
    4. feedback_submissions (unique session_id, created_at, overall_experience)
    5. review_link_clicks (created_at, session_id)
    6. subscription_records (status, expires_at)
    """
    try:
        # 1. restaurant_settings: unique slug index
        await db[COLLECTION_RESTAURANT_SETTINGS].create_index(
            [("slug", pymongo.ASCENDING)],
            unique=True,
            name="idx_restaurant_slug_unique",
        )

        # 2. admin_users: unique email index
        await db[COLLECTION_ADMIN_USERS].create_index(
            [("email", pymongo.ASCENDING)],
            unique=True,
            name="idx_admin_email_unique",
        )

        # 3. qr_scans: created_at index for monthly analytics, session_id, and ip_hash for unique stats
        await db[COLLECTION_QR_SCANS].create_index(
            [("created_at", pymongo.DESCENDING)],
            name="idx_qr_scans_created_at",
        )
        await db[COLLECTION_QR_SCANS].create_index(
            [("session_id", pymongo.ASCENDING)],
            name="idx_qr_scans_session_id",
        )
        await db[COLLECTION_QR_SCANS].create_index(
            [("ip_hash", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            name="idx_qr_scans_ip_created",
        )
        await db[COLLECTION_QR_SCANS].create_index(
            [("is_bot", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
            name="idx_qr_scans_bot_created",
        )

        # 4. feedback_submissions: UNIQUE session_id to prevent duplicates, created_at, overall
        await db[COLLECTION_FEEDBACK_SUBMISSIONS].create_index(
            [("session_id", pymongo.ASCENDING)],
            unique=True,
            name="idx_feedback_session_id_unique",
        )
        await db[COLLECTION_FEEDBACK_SUBMISSIONS].create_index(
            [("created_at", pymongo.DESCENDING)],
            name="idx_feedback_created_at",
        )
        await db[COLLECTION_FEEDBACK_SUBMISSIONS].create_index(
            [("overall_experience", pymongo.ASCENDING)],
            name="idx_feedback_overall",
        )

        # 5. review_link_clicks: created_at, session_id
        await db[COLLECTION_REVIEW_LINK_CLICKS].create_index(
            [("created_at", pymongo.DESCENDING)],
            name="idx_review_clicks_created_at",
        )
        await db[COLLECTION_REVIEW_LINK_CLICKS].create_index(
            [("session_id", pymongo.ASCENDING)],
            name="idx_review_clicks_session_id",
        )

        # 6. subscription_records: status, expires_at, created_at
        await db[COLLECTION_SUBSCRIPTION_RECORDS].create_index(
            [("status", pymongo.ASCENDING)],
            name="idx_subscription_status",
        )
        await db[COLLECTION_SUBSCRIPTION_RECORDS].create_index(
            [("expires_at", pymongo.DESCENDING)],
            name="idx_subscription_expires_at",
        )
        await db[COLLECTION_SUBSCRIPTION_RECORDS].create_index(
            [("created_at", pymongo.DESCENDING)],
            name="idx_subscription_created_at",
        )

        # 7. payment_records: provider_order_id, provider_payment_id, status, created_at, idempotency
        await db[COLLECTION_PAYMENT_RECORDS].create_index(
            [("provider_order_id", pymongo.ASCENDING)],
            name="idx_payment_order_id",
        )
        await db[COLLECTION_PAYMENT_RECORDS].create_index(
            [("provider_payment_id", pymongo.ASCENDING)],
            sparse=True,
            name="idx_payment_provider_id",
        )
        await db[COLLECTION_PAYMENT_RECORDS].create_index(
            [("status", pymongo.ASCENDING)],
            name="idx_payment_status",
        )
        await db[COLLECTION_PAYMENT_RECORDS].create_index(
            [("created_at", pymongo.DESCENDING)],
            name="idx_payment_created_at",
        )
        await db[COLLECTION_PAYMENT_RECORDS].create_index(
            [("idempotency_key", pymongo.ASCENDING)],
            sparse=True,
            unique=True,
            name="idx_payment_idempotency_unique",
        )

        logger.info("MongoDB indexes successfully created/verified across all 7 collections.")
    except Exception as exc:
        logger.warning(f"Error creating MongoDB indexes: {exc}")
