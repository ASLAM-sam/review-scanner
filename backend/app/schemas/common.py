"""
Common API Request & Response Schemas
"""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None


class MessageResponse(BaseModel):
    success: bool = True
    message: str

