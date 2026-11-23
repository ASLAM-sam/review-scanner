"""
Application Configuration Module
Independent Single-Tenant Deployment Configuration
"""

from typing import List, Optional, Union
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "Restaurant QR Feedback & Review Assistance System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "insecure-default-secret-key-change-in-production-min-32-chars-long"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long for cryptographic security.")
        return v

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    ALLOWED_ORIGIN_REGEX: Optional[str] = r"^https:\/\/.*\.vercel\.app$"
    COOKIE_SAMESITE: str = "lax"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database settings (Independent DB per restaurant)
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "restaurant_db"
    MONGODB_CONNECT_TIMEOUT_MS: int = 5000

    # Authentication & JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    INITIAL_ADMIN_EMAIL: str = "admin@restaurant.com"
    INITIAL_ADMIN_PASSWORD: str = "Admin@Secure123"

    # Restaurant Installation Settings (Initial Defaults for this Installation)
    RESTAURANT_NAME: str = "Paradise Restaurant"
    RESTAURANT_SLUG: str = "paradise-restaurant"
    RESTAURANT_DESCRIPTION: str = "Fine Dining & Authentic Cuisine"
    RESTAURANT_LOGO_URL: str = ""
    RESTAURANT_PRIMARY_COLOR: str = "#16a34a"
    RESTAURANT_SECONDARY_COLOR: str = "#15803d"
    RESTAURANT_GOOGLE_REVIEW_URL: str = "https://g.page/r/your-google-review-link"
    RESTAURANT_QR_BASE_URL: str = "http://localhost:3000/r"
    RESTAURANT_CONTACT_PHONE: str = ""
    RESTAURANT_CONTACT_EMAIL: str = ""
    RESTAURANT_ADDRESS: str = ""
    RESTAURANT_TIMEZONE: str = "Asia/Kolkata"

    @field_validator("RESTAURANT_TIMEZONE")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            import zoneinfo
            zoneinfo.ZoneInfo(v)
            return v
        except Exception:
            raise ValueError(f"Invalid IANA timezone name: {v}. Must be a valid timezone like 'Asia/Kolkata' or 'America/New_York'.")

    @field_validator("RESTAURANT_GOOGLE_REVIEW_URL", "RESTAURANT_QR_BASE_URL")
    @classmethod
    def validate_urls(cls, v: str) -> str:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"URL must start with http:// or https://: {v}")
        return v

    # Security & Rate Limiting
    MAX_REQUEST_BODY_SIZE: int = 1_048_576  # 1 MB
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_SCAN_PER_MINUTE: int = 60
    RATE_LIMIT_PAYMENT_PER_MINUTE: int = 15
    RATE_LIMIT_WEBHOOK_PER_MINUTE: int = 60

    # Subscription & Billing Configuration
    SUBSCRIPTION_REQUIRED: bool = True
    SUBSCRIPTION_STATUS_DEFAULT: str = "active"
    ALLOW_COMPLIMENTARY_TRIAL: bool = False
    SUBSCRIPTION_PLAN_NAME: str = "Standard Monthly"
    SUBSCRIPTION_PLAN_ID: str = "plan_standard_monthly"
    SUBSCRIPTION_AMOUNT_PAISE: int = 24900  # ₹249 per month in integer paise
    SUBSCRIPTION_BILLING_INTERVAL: str = "monthly"
    PAYMENT_CURRENCY: str = "INR"
    SUBSCRIPTION_GRACE_DAYS: int = 0  # Zero grace days by default; configurable

    # Payment Gateway Configuration (Razorpay)
    PAYMENT_PROVIDER: str = "razorpay"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    @model_validator(mode="after")
    def validate_production_invariants(self) -> "Settings":
        """Enforce strict security and billing invariants for production deployment."""
        if self.ENVIRONMENT == "production":
            if "insecure-default" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("In production, SECRET_KEY must be a unique, cryptographically random key of >=32 chars.")
            # Commercial installations must strictly require subscription in production
            self.SUBSCRIPTION_REQUIRED = True
            # In production, default must be inactive unless explicitly granted a complimentary trial
            if self.SUBSCRIPTION_STATUS_DEFAULT == "active" and not self.ALLOW_COMPLIMENTARY_TRIAL:
                self.SUBSCRIPTION_STATUS_DEFAULT = "inactive"
        return self


settings = Settings()
