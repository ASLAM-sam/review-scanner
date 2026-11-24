"""
Main Application Entrypoint
FastAPI Restaurant QR Feedback & Google Review Assistance System
Single-Tenant Independent Installation Architecture
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

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
    docs_url="/docs" if (settings.DEBUG or settings.ENABLE_DOCS) else None,
    redoc_url="/redoc" if (settings.DEBUG or settings.ENABLE_DOCS) else None,
    openapi_url="/openapi.json" if (settings.DEBUG or settings.ENABLE_DOCS) else None,
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


# 6. Root & Health check endpoints
@app.get("/", tags=["Root"])
@app.get(f"{settings.API_V1_PREFIX}", tags=["Root"])
@app.get("/api", tags=["Root"])
async def root_index(request: Request):
    """Root status and API information endpoint."""
    db = get_database()
    if db is None:
        await connect_to_mongo()
        db = get_database()
    db_status = "connected" if db is not None else "disconnected"

    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{settings.APP_NAME}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 1.5rem; display: flex; align-items: center; justify-content: center; min-height: 90vh; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 1rem; padding: 2.25rem; max-width: 520px; width: 100%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); text-align: center; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.5rem; background: #064e3b; color: #34d399; font-weight: 600; font-size: 0.85rem; padding: 0.35rem 0.85rem; border-radius: 9999px; margin-bottom: 1.25rem; }}
    .dot {{ width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }}
    h1 {{ font-size: 1.35rem; margin: 0 0 0.5rem; color: #fff; font-weight: 700; }}
    p {{ color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin: 0 0 1.5rem; }}
    .links {{ display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1.5rem; }}
    .btn {{ display: block; text-align: center; text-decoration: none; padding: 0.75rem 1rem; border-radius: 0.5rem; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; }}
    .btn-primary {{ background: #10b981; color: #022c22; }}
    .btn-primary:hover {{ background: #059669; color: #fff; }}
    .btn-secondary {{ background: #334155; color: #f1f5f9; }}
    .btn-secondary:hover {{ background: #475569; }}
    .meta {{ border-top: 1px solid #334155; margin-top: 1.75rem; padding-top: 1.25rem; font-size: 0.8rem; color: #64748b; display: flex; justify-content: space-between; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge"><span class="dot"></span>API Online &amp; Healthy</div>
    <h1>Restaurant QR Feedback System</h1>
    <p>FastAPI Backend is running successfully on Vercel Serverless.</p>
    <div class="links">
      <a class="btn btn-primary" href="/docs">Open Interactive API Docs (Swagger)</a>
      <a class="btn btn-secondary" href="{settings.API_V1_PREFIX}/health">View JSON Health Check</a>
    </div>
    <div class="meta">
      <span>Restaurant: <strong>{settings.RESTAURANT_NAME}</strong></span>
      <span>Database: <strong>{db_status}</strong></span>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_content, status_code=200)

    return {
        "status": "online",
        "message": "Restaurant QR Feedback & Review Assistance System API is online and healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "restaurant": settings.RESTAURANT_NAME,
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_PREFIX}/health",
    }


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

