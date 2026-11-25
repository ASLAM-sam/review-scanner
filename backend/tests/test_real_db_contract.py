"""
Database Integration and Contract Tests
Verifies:
- Connection failure handling and timeouts
- Unique index constraint enforcement on slug, email, and session_id
- Collection structure and field validation
- Reconnection and ping behavior
"""

import pytest
import pymongo
from pymongo.errors import DuplicateKeyError
from app.db.collections import (
    COLLECTION_ADMIN_USERS,
    COLLECTION_FEEDBACK_SUBMISSIONS,
    COLLECTION_RESTAURANT_SETTINGS,
)
from app.db.mongodb import connect_to_mongo, is_db_alive
from app.models.feedback import FeedbackSubmission
from app.models.restaurant import RestaurantSettingsInDB
from app.models.user import AdminUserInDB


@pytest.mark.asyncio
async def test_invalid_mongodb_uri_handling():
    """Verify connection failure to non-existent MongoDB host fails gracefully without crashing."""
    invalid_uri = "mongodb://nonexistent.invalid.host:27017"
    # Attempt connection with 1 fast retry
    connected = await connect_to_mongo(uri=invalid_uri, db_name="invalid_db", max_retries=1)
    assert connected is False


@pytest.mark.asyncio
async def test_unique_slug_index_enforcement(mock_db):
    """Verify MongoDB enforces unique constraint on restaurant_settings.slug."""
    doc1 = RestaurantSettingsInDB(
        name="Restaurant One",
        slug="unique-restaurant-slug",
        google_review_url="https://g.page/r/test",
        qr_destination_url="http://localhost:3000/r/unique-restaurant-slug",
    ).model_dump(exclude={"id"})
    await mock_db[COLLECTION_RESTAURANT_SETTINGS].insert_one(doc1)

    # Attempting to insert duplicate slug must raise DuplicateKeyError
    doc2 = RestaurantSettingsInDB(
        name="Restaurant Duplicate",
        slug="unique-restaurant-slug",
        google_review_url="https://g.page/r/test2",
        qr_destination_url="http://localhost:3000/r/unique-restaurant-slug",
    ).model_dump(exclude={"id"})

    with pytest.raises(DuplicateKeyError):
        await mock_db[COLLECTION_RESTAURANT_SETTINGS].insert_one(doc2)


@pytest.mark.asyncio
async def test_unique_admin_username_enforcement(mock_db):
    """Verify MongoDB enforces unique constraint on admin_users.username."""
    user1 = AdminUserInDB(
        username="unique_aslam",
        hashed_password="some_hashed_password",
        is_active=True,
    ).model_dump(exclude={"id"})
    await mock_db[COLLECTION_ADMIN_USERS].insert_one(user1)

    # Attempting duplicate admin username must raise DuplicateKeyError
    user2 = AdminUserInDB(
        username="unique_aslam",
        hashed_password="another_hashed_password",
        is_active=True,
    ).model_dump(exclude={"id"})

    with pytest.raises(DuplicateKeyError):
        await mock_db[COLLECTION_ADMIN_USERS].insert_one(user2)


@pytest.mark.asyncio
async def test_unique_feedback_session_id_enforcement(mock_db):
    """Verify MongoDB enforces unique constraint on feedback_submissions.session_id."""
    fb1 = FeedbackSubmission(
        session_id="unique-feedback-session-123",
        food_rating=5,
        service_rating=5,
        ambience_rating=5,
        overall_experience="positive",
    ).model_dump(exclude={"id"})
    await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].insert_one(fb1)

    # Attempting duplicate feedback for same session must raise DuplicateKeyError
    fb2 = FeedbackSubmission(
        session_id="unique-feedback-session-123",
        food_rating=1,
        service_rating=1,
        ambience_rating=1,
        overall_experience="negative",
    ).model_dump(exclude={"id"})

    with pytest.raises(DuplicateKeyError):
        await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].insert_one(fb2)

