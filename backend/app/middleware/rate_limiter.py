"""
In-Memory Rate Limiting & Abuse Protection Middleware
Secured with safe client IP extraction, memory-bounded prune, and route-specific abuse thresholds.
"""

import time
import ipaddress
from collections import defaultdict
from typing import Dict, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.core.config import settings
from app.core.logging import logger


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address safely.
    Checks CF-Connecting-IP, X-Real-IP, and X-Forwarded-For with format validation.
    """
    # 1. Cloudflare header
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip and _is_valid_ip(cf_ip.strip()):
        return cf_ip.strip()

    # 2. X-Real-IP header (common in Nginx / Caddy reverse proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and _is_valid_ip(real_ip.strip()):
        return real_ip.strip()

    # 3. X-Forwarded-For header (leftmost IP is original client)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        first_ip = forwarded.split(",")[0].strip()
        if _is_valid_ip(first_ip):
            return first_ip

    # 4. Direct peer connection
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _is_valid_ip(ip_str: str) -> bool:
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Separate buckets for different categories: category -> ip -> timestamps
        self.request_history: Dict[str, Dict[str, List[float]]] = {
            "default": defaultdict(list),
            "auth": defaultdict(list),
            "feedback": defaultdict(list),
            "scan": defaultdict(list),
            "payment": defaultdict(list),
            "webhook": defaultdict(list),
        }
        self.window_seconds = 60
        self.last_cleanup = time.time()
        self.max_tracked_ips = 10_000

    def _cleanup_expired(self, now: float) -> None:
        """Periodic garbage collection of expired IP tracking history to prevent memory leak."""
        if now - self.last_cleanup < 30:
            return

        self.last_cleanup = now
        cutoff = now - self.window_seconds

        for bucket_name, bucket in self.request_history.items():
            stale_ips = []
            for ip, timestamps in list(bucket.items()):
                valid_ts = [ts for ts in timestamps if ts > cutoff]
                if valid_ts:
                    bucket[ip] = valid_ts
                else:
                    stale_ips.append(ip)

            for ip in stale_ips:
                bucket.pop(ip, None)

        # Cap memory if too many distinct IPs under flood
        for bucket in self.request_history.values():
            if len(bucket) > self.max_tracked_ips:
                bucket.clear()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting on preflight, health checks, or docs
        path = request.url.path
        if request.method == "OPTIONS" or path in ["/health", "/", "/api/v1/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Skip rate limiting in automated test environment
        if settings.ENVIRONMENT == "test":
            return await call_next(request)

        now = time.time()
        self._cleanup_expired(now)

        client_ip = get_client_ip(request)

        # Determine route-specific rate category
        if "/auth/login" in path:
            category = "auth"
            limit = 10  # Max 10 login attempts per minute (brute-force defense)
            window = 60
        elif "/subscription/create-order" in path or "/subscription/verify-payment" in path:
            category = "payment"
            limit = settings.RATE_LIMIT_PAYMENT_PER_MINUTE
            window = 60
        elif "/webhook" in path:
            category = "webhook"
            limit = settings.RATE_LIMIT_WEBHOOK_PER_MINUTE
            window = 60
        elif "/public/feedback" in path:
            category = "feedback"
            limit = 10  # Max 10 feedback submissions per minute
            window = 60
        elif "/qr/scan" in path:
            category = "scan"
            limit = settings.RATE_LIMIT_SCAN_PER_MINUTE
            window = 60
        else:
            category = "default"
            limit = settings.RATE_LIMIT_PER_MINUTE
            window = 60

        bucket = self.request_history[category][client_ip]
        cutoff = now - window
        # Clean this specific IP's list
        self.request_history[category][client_ip] = [ts for ts in bucket if ts > cutoff]
        updated_bucket = self.request_history[category][client_ip]

        if len(updated_bucket) >= limit:
            logger.warning(
                f"Rate limit exceeded for client {client_ip} on category '{category}' ({len(updated_bucket)}/{limit})"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please slow down and try again shortly.",
                },
                headers={"Retry-After": str(window)},
            )

        self.request_history[category][client_ip].append(now)
        return await call_next(request)
