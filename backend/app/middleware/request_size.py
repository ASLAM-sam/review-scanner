"""
Request Size Limiter Middleware
Blocks oversized payloads to mitigate memory exhaustion and denial-of-service.
Secured against Content-Length header omission and chunked transfer encoding bypass.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import Message
from app.core.config import settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Fast check if Content-Length header is present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.MAX_REQUEST_BODY_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "message": f"Payload too large. Maximum allowed size is {settings.MAX_REQUEST_BODY_SIZE} bytes.",
                        },
                    )
            except ValueError:
                pass

        # 2. Defensive streaming counter to prevent chunked encoding bypass
        # Wrap request._receive to count actual bytes streamed
        bytes_received = 0
        original_receive = request._receive

        async def counting_receive() -> Message:
            nonlocal bytes_received
            message = await original_receive()
            if message.get("type") == "http.request":
                chunk_len = len(message.get("body", b""))
                bytes_received += chunk_len
                if bytes_received > settings.MAX_REQUEST_BODY_SIZE:
                    raise RequestEntityTooLargeException()
            return message

        request._receive = counting_receive

        try:
            return await call_next(request)
        except RequestEntityTooLargeException:
            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "message": f"Payload too large. Maximum allowed size is {settings.MAX_REQUEST_BODY_SIZE} bytes.",
                },
            )


class RequestEntityTooLargeException(Exception):
    """Raised when streaming body exceeds maximum allowed bytes."""
    pass
