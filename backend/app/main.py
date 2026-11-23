"""
Main Application Entrypoint
FastAPI Restaurant QR Feedback & Google Review Assistance System
Single-Tenant Independent Installation Architecture
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import logger
from app.db.mongodb import close_mongo_connection, connect_to_mongo, get_database
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.auth_service import auth_service
from app.services.restaurant_service import restaurant_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' environment...")
    
    # 0. Critical production security gate
    if settings.ENVIRONMENT == "production":
        if "insecure-default" in settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: "
                "Default or insufficient SECRET_KEY detected in production! "
                "You must configure a unique, cryptographically random SECRET_KEY (min 32 chars) in your .env file."
            )

    # 1. Connect to MongoDB
    connected = await connect_to_mongo()
    if connected:
        db = get_database()
        # 2. Seed initial restaurant configuration if empty
        await restaurant_service.ensure_initial_settings(db)
        # 3. Seed initial admin user if empty
        await auth_service.ensure_initial_admin(db)
        logger.info("Database and initial credentials verified.")
    else:
        logger.warning("Application initialized without live database. Operating with in-memory fallbacks.")

    yield

    # Teardown
    logger.info("Shutting down application...")
    await close_mongo_connection()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Commercial Restaurant QR Feedback & Review Assistance System - Independent Single-Tenant Backend",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 1. Security Headers Middleware (OWASP protection)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request Body Size Limiter (DOS protection)
app.add_middleware(RequestSizeLimitMiddleware)

# 3. Rate Limiter Middleware
app.add_middleware(RateLimiterMiddleware)

# 4. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

# 5. Global Exception Handler (Prevent secret or stack trace leaks)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=settings.DEBUG)
    if settings.DEBUG:
        detail_msg = str(exc)
    else:
        detail_msg = "An internal server error occurred. Please contact restaurant support."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": detail_msg,
        },
    )


# 6. Health check endpoints
@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
async def health_check():
    """Health check for container orchestrators, serverless probes and monitoring."""
    db = get_database()
    if db is None:
        await connect_to_mongo()
        db = get_database()
    db_status = "connected" if db is not None else "disconnected"
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "restaurant": settings.RESTAURANT_NAME,
    }


# 7. Mount API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

