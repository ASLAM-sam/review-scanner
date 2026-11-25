"""
Authentication API Schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminUserResponse(BaseModel):
    id: Optional[str] = None
    username: str
    full_name: Optional[str] = None
    is_active: bool

