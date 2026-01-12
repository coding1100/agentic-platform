from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re


class ApiKeyCreate(BaseModel):
    agent_id: Optional[UUID] = Field(None, description="Agent ID this API key is for. If null, key works for all agents.")
    name: str = Field(..., description="User-friendly name for the API key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    rate_limit_per_minute: int = Field(60, ge=1, le=1000, description="Rate limit per minute")
    allowed_origins: Optional[List[str]] = Field(
        None, 
        description="List of allowed origins (e.g., ['https://example.com']). If null or empty, allows all origins."
    )
    
    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate origin format: must be https:// or http:// followed by domain (no ports)."""
        if v is None:
            return v
        
        if len(v) == 0:
            return None  # Empty list = allow all
        
        origin_pattern = re.compile(r'^https?://[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
        
        validated_origins = []
        for origin in v:
            origin = origin.strip().rstrip('/')
            
            # Check format
            if not origin_pattern.match(origin):
                raise ValueError(f"Invalid origin format: {origin}. Must be in format https://example.com (no ports, no paths)")
            
            # Ensure no ports
            if ':' in origin.split('://')[1]:
                raise ValueError(f"Origin must not include port: {origin}")
            
            validated_origins.append(origin)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_origins = []
        for origin in validated_origins:
            if origin.lower() not in seen:
                seen.add(origin.lower())
                unique_origins.append(origin)
        
        return unique_origins if unique_origins else None


class ApiKeyResponse(BaseModel):
    id: UUID
    agent_id: Optional[UUID]  # Null if universal key
    name: str
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    rate_limit_per_minute: int
    total_requests: int
    allowed_origins: Optional[List[str]] = None  # Null or empty = allow all origins
    key: Optional[str] = None  # Only included when creating a new key
    agent_slug: Optional[str] = None  # Agent slug for URL generation

    class Config:
        from_attributes = True


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Update the API key name")
    allowed_origins: Optional[List[str]] = Field(
        None, 
        description="Update allowed origins. Set to empty list to allow all origins."
    )
    is_active: Optional[bool] = Field(None, description="Update active status")
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000, description="Update rate limit")
    
    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate origin format: must be https:// or http:// followed by domain (no ports)."""
        if v is None:
            return v
        
        if len(v) == 0:
            return []  # Empty list = allow all (will be converted to None in endpoint)
        
        origin_pattern = re.compile(r'^https?://[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
        
        validated_origins = []
        for origin in v:
            origin = origin.strip().rstrip('/')
            
            # Check format
            if not origin_pattern.match(origin):
                raise ValueError(f"Invalid origin format: {origin}. Must be in format https://example.com (no ports, no paths)")
            
            # Ensure no ports
            if ':' in origin.split('://')[1]:
                raise ValueError(f"Origin must not include port: {origin}")
            
            validated_origins.append(origin)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_origins = []
        for origin in validated_origins:
            if origin.lower() not in seen:
                seen.add(origin.lower())
                unique_origins.append(origin)
        
        return unique_origins if unique_origins else []


class ApiKeyUsageStats(BaseModel):
    total_requests: int
    last_used_at: Optional[datetime]
    requests_today: int
    requests_this_month: int

