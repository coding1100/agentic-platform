from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ApiKeyCreate(BaseModel):
    agent_id: UUID = Field(..., description="Agent ID this API key is for")
    name: str = Field(..., description="User-friendly name for the API key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    rate_limit_per_minute: int = Field(60, ge=1, le=1000, description="Rate limit per minute")


class ApiKeyResponse(BaseModel):
    id: UUID
    agent_id: UUID
    name: str
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    rate_limit_per_minute: int
    total_requests: int
    key: Optional[str] = None  # Only included when creating a new key
    agent_slug: Optional[str] = None  # Agent slug for URL generation

    class Config:
        from_attributes = True


class ApiKeyUsageStats(BaseModel):
    total_requests: int
    last_used_at: Optional[datetime]
    requests_today: int
    requests_this_month: int

