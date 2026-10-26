
from typing import Any, Optional

from pydantic import BaseModel, Field


class MarineQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)


class RouteRequest(BaseModel):
    origin: str = Field(..., min_length=2, max_length=150)
    destination: str = Field(..., min_length=2, max_length=150)


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
