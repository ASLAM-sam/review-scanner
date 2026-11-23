"""
QR Service Tests
Verifies stable URL formatting, IP hashing anonymization, and QR asset rendering.
"""

import pytest
from app.services.qr_service import qr_service
from app.services.subscription_service import subscription_service


def test_qr_asset_generation():
    test_url = "https://restaurant-paradise.com/r/paradise"
    svg_str, data_url = qr_service.generate_qr_assets(test_url)
    assert "<svg" in svg_str
    assert data_url.startswith("data:image/png;base64,")


def test_ip_hashing_anonymity():
    ip = "192.168.1.50"
    hashed_ip = qr_service.hash_ip(ip)
    assert hashed_ip is not None
    assert hashed_ip != ip
    assert len(hashed_ip) == 64  # SHA-256 length
    # Same IP produces identical hash with same secret
    assert qr_service.hash_ip(ip) == hashed_ip
    # None IP produces None
    assert qr_service.hash_ip(None) is None


@pytest.mark.asyncio
async def test_subscription_status_check(mock_db):
    status = await subscription_service.get_current_status(mock_db)
    assert status in ["active", "expired", "trial", "suspended"]

