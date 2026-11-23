"""
QR Management Service
Handles dynamic QR generation, scan logging, crawler filtering, and destination resolution.
"""

import base64
import hashlib
import io
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import segno

from app.core.config import settings
from app.core.logging import logger
from app.db.collections import COLLECTION_QR_SCANS
from app.models.qr_scan import QRScanEvent
from app.services.restaurant_service import restaurant_service
from app.services.subscription_service import subscription_service

# Pattern to identify automated web scrapers, link previewers, and crawlers
BOT_PATTERN = re.compile(
    r"(googlebot|bingbot|yandex|duckduckbot|slurp|baiduspider|facebookexternalhit|whatsapp|"
    r"telegrambot|twitterbot|linkedinbot|embedly|quora link preview|showyoubot|outbrain|"
    r"pinterest|slackbot|vkshare|w3c_validator|curl|wget|python-requests|aiohttp|scrapy)",
    re.IGNORECASE,
)


class QRService:
    @staticmethod
    def hash_ip(ip_address: Optional[str]) -> Optional[str]:
        """Generate one-way salted hash for IP address to maintain customer privacy."""
        if not ip_address:
            return None
        salt = settings.SECRET_KEY[:16]
        return hashlib.sha256(f"{salt}:{ip_address}".encode("utf-8")).hexdigest()

    @staticmethod
    def is_bot_user_agent(user_agent: Optional[str]) -> bool:
        """Identify automated search crawlers, bots, and link preview generators."""
        if not user_agent:
            return False
        return bool(BOT_PATTERN.search(user_agent))

    @staticmethod
    def generate_qr_assets(url: str) -> Tuple[str, str]:
        """
        Generate both SVG markup and base64 PNG data URL for a given URL using segno.
        Pure Python, zero native OS dependencies.
        """
        qr = segno.make(url, error="M")

        # 1. Generate SVG string (segno writes bytes to BytesIO)
        svg_buffer = io.BytesIO()
        qr.save(svg_buffer, kind="svg", scale=8, dark="#111827", light="#ffffff")
        svg_string = svg_buffer.getvalue().decode("utf-8")

        # 2. Generate PNG Data URL
        png_buffer = io.BytesIO()
        qr.save(png_buffer, kind="png", scale=8, dark="#111827", light="#ffffff")
        png_base64 = base64.b64encode(png_buffer.getvalue()).decode("utf-8")
        data_url = f"data:image/png;base64,{png_base64}"

        return svg_string, data_url

    @classmethod
    async def record_scan(
        cls,
        db: Optional[AsyncIOMotorDatabase],
        client_ip: Optional[str],
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Record a QR scan event.
        Filters automated crawlers and distinguishes new customer scans from browser refreshes.
        Returns: (session_id, destination_url, subscription_status)
        """
        restaurant = await restaurant_service.get_settings(db)
        sub_status = await subscription_service.get_current_status(db)

        is_bot = cls.is_bot_user_agent(user_agent)
        is_unique = not is_bot
        effective_session_id = session_id or str(uuid.uuid4())
        hashed_ip = cls.hash_ip(client_ip)

        if db is not None:
            try:
                # 1. If client sent an existing session_id, check if already recorded
                if session_id:
                    existing = await db[COLLECTION_QR_SCANS].find_one({"session_id": session_id})
                    if existing:
                        # This is a browser reload / refresh of the existing session
                        is_unique = False

                # 2. If no session_id provided, check if same hashed IP scanned in last 5 minutes
                elif hashed_ip:
                    five_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
                    recent_ip_scan = await db[COLLECTION_QR_SCANS].find_one(
                        {
                            "ip_hash": hashed_ip,
                            "created_at": {"$gte": five_mins_ago},
                            "is_bot": False,
                        }
                    )
                    if recent_ip_scan:
                        # Repeated scan in quick succession from the same device
                        is_unique = False
                        # Reuse the recent session to avoid fragmenting the feedback journey
                        effective_session_id = recent_ip_scan.get("session_id", effective_session_id)

                scan_event = QRScanEvent(
                    session_id=effective_session_id,
                    ip_hash=hashed_ip,
                    user_agent=user_agent[:500] if user_agent else None,
                    referrer=referrer[:500] if referrer else None,
                    is_unique=is_unique,
                    is_bot=is_bot,
                )
                await db[COLLECTION_QR_SCANS].insert_one(
                    scan_event.model_dump(by_alias=False, exclude={"id"})
                )
                logger.info(
                    f"Logged QR scan session: {effective_session_id} "
                    f"(Unique: {is_unique}, Bot: {is_bot}, Status: {sub_status})"
                )
            except Exception as exc:
                logger.warning(f"Error persisting QR scan event: {exc}")

        destination = restaurant.qr_destination_url or f"{settings.RESTAURANT_QR_BASE_URL.rstrip('/')}/{restaurant.slug}"
        return effective_session_id, destination, sub_status


qr_service = QRService()
