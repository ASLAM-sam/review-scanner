"""
Pytest Test Fixtures and Configuration
Uses mongomock_motor for high-fidelity, in-memory MongoDB async testing.
"""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

# Set environment before loading app
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum-length-for-testing"
os.environ["MONGODB_DB_NAME"] = "test_restaurant_db"

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.collections import COLLECTION_ADMIN_USERS, COLLECTION_RESTAURANT_SETTINGS
from app.db.mongodb import init_db_indexes
from app.main import app
from app.api.deps import get_db
from app.models.restaurant import RestaurantSettingsInDB
from app.models.user import AdminUserInDB


@pytest_asyncio.fixture
async def mock_db():
    """Create an isolated, in-memory MongoDB database instance."""
    mock_client = AsyncMongoMockClient()
    db = mock_client[settings.MONGODB_DB_NAME]
    
    # Initialize indexes
    await init_db_indexes(db)

    # Seed restaurant settings
    restaurant = RestaurantSettingsInDB(
        name="Paradise Test Restaurant",
        slug="paradise-test-restaurant",
        description="Fine Dining Test",
        logo_url="https://example.com/logo.png",
        primary_color="#16a34a",
        secondary_color="#15803d",
        google_review_url="https://g.page/r/test-review",
        qr_destination_url="http://localhost:3000/r/paradise-test-restaurant",
        is_active=True,
    )
    res_doc = restaurant.model_dump(by_alias=False, exclude={"id"})
    await db[COLLECTION_RESTAURANT_SETTINGS].insert_one(res_doc)

    # Seed admin user
    admin = AdminUserInDB(
        username="aslam",
        hashed_password=get_password_hash("aslam0077"),
        full_name="Aslam (Test Administrator)",
        is_active=True,
    )
    admin_doc = admin.model_dump(by_alias=False, exclude={"id"})
    await db[COLLECTION_ADMIN_USERS].insert_one(admin_doc)

    return db


@pytest_asyncio.fixture
async def async_client(mock_db):
    """Create an AsyncClient with database dependency overridden to mock_db."""
    async def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_token():
    """Generate a valid JWT token for the seeded test admin."""
    return create_access_token(data={"sub": "aslam"})


@pytest.fixture
def auth_headers(admin_token):
    """Authorization header dictionary."""
    return {"Authorization": f"Bearer {admin_token}"}
