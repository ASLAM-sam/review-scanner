"""
Configuration Tests
Verifies environment loading, settings defaults, and CORS origin validation.
"""

from app.core.config import Settings


def test_settings_defaults():
    s = Settings(
        SECRET_KEY="a-very-long-test-secret-key-32-chars-long",
        RESTAURANT_NAME="Test Bistro",
        RESTAURANT_SLUG="test-bistro",
    )
    assert s.RESTAURANT_NAME == "Test Bistro"
    assert s.RESTAURANT_SLUG == "test-bistro"
    assert s.API_V1_PREFIX == "/api/v1"
    assert s.ALGORITHM == "HS256"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_cors_origins_parsing():
    s = Settings(
        SECRET_KEY="a-very-long-test-secret-key-32-chars-long",
        ALLOWED_ORIGINS="http://localhost:3000, https://restaurant.com",
    )
    assert isinstance(s.ALLOWED_ORIGINS, list)
    assert "http://localhost:3000" in s.ALLOWED_ORIGINS
    assert "https://restaurant.com" in s.ALLOWED_ORIGINS


def test_secret_key_presence():
    s = Settings(SECRET_KEY="custom-secure-secret-key-sample-value")
    assert len(s.SECRET_KEY) >= 32

