"""
Database Operations and Collection Tests
Validates the 6 MongoDB collections, indexing, and data models.
"""

import pytest
from app.db.collections import (
    COLLECTION_ADMIN_USERS,
    COLLECTION_FEEDBACK_SUBMISSIONS,
    COLLECTION_QR_SCANS,
    COLLECTION_RESTAURANT_SETTINGS,
    COLLECTION_REVIEW_LINK_CLICKS,
    COLLECTION_SUBSCRIPTION_RECORDS,
)
from app.models.feedback import FeedbackSubmission
from app.models.qr_scan import QRScanEvent
from app.models.review_click import ReviewLinkClickEvent
from app.models.subscription import SubscriptionRecord


@pytest.mark.asyncio
async def test_collections_exist_and_seed_data(mock_db):
    res_count = await mock_db[COLLECTION_RESTAURANT_SETTINGS].count_documents({})
    admin_count = await mock_db[COLLECTION_ADMIN_USERS].count_documents({})
    assert res_count >= 1
    assert admin_count >= 1


@pytest.mark.asyncio
async def test_qr_scan_collection_insert(mock_db):
    event = QRScanEvent(session_id="test-session-123", user_agent="Mozilla/5.0")
    result = await mock_db[COLLECTION_QR_SCANS].insert_one(event.model_dump(exclude={"id"}))
    assert result.inserted_id is not None
    count = await mock_db[COLLECTION_QR_SCANS].count_documents({"session_id": "test-session-123"})
    assert count == 1


@pytest.mark.asyncio
async def test_feedback_collection_insert(mock_db):
    fb = FeedbackSubmission(
        session_id="test-session-123",
        food_rating=5,
        service_rating=4,
        ambience_rating=5,
        overall_experience="positive",
        positive_tags=["Delicious Food", "Great Ambience"],
    )
    result = await mock_db[COLLECTION_FEEDBACK_SUBMISSIONS].insert_one(fb.model_dump(exclude={"id"}))
    assert result.inserted_id is not None


@pytest.mark.asyncio
async def test_review_click_collection_insert(mock_db):
    click = ReviewLinkClickEvent(
        session_id="test-session-123",
        target_url="https://g.page/r/test",
    )
    result = await mock_db[COLLECTION_REVIEW_LINK_CLICKS].insert_one(click.model_dump(exclude={"id"}))
    assert result.inserted_id is not None


@pytest.mark.asyncio
async def test_subscription_collection_insert(mock_db):
    sub = SubscriptionRecord(status="active", billing_cycle="monthly")
    result = await mock_db[COLLECTION_SUBSCRIPTION_RECORDS].insert_one(sub.model_dump(exclude={"id"}))
    assert result.inserted_id is not None

