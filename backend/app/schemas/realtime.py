from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class EmbedDeploymentUpsert(BaseModel):
    is_active: bool = True
    allowed_origins: Optional[List[str]] = Field(
        None,
        description="Allowed web origins for this embed deployment. Empty or null means allow all.",
    )
    token_ttl_seconds: Optional[int] = Field(
        None,
        ge=60,
        le=3600,
        description="Token TTL in seconds for participant join tokens.",
    )
    max_concurrent_sessions: Optional[int] = Field(
        None,
        ge=1,
        le=200,
        description="Maximum concurrent active sessions allowed for this deployment.",
    )
    room_name_prefix: Optional[str] = Field(
        None,
        min_length=3,
        max_length=64,
        description="Optional room prefix used for generated room names.",
    )

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None

        if len(v) == 0:
            return None

        validated_origins: list[str] = []
        for origin in v:
            normalized = origin.strip().rstrip("/")

            parsed = urlparse(normalized)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
                raise ValueError(
                    (
                        f"Invalid origin format: {origin}. "
                        "Must be a valid origin like https://example.com or http://localhost:5173"
                    )
                )
            if parsed.username or parsed.password:
                raise ValueError(f"Origin must not include user info: {origin}")
            if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.params:
                raise ValueError(f"Origin must not include path, query, or fragment: {origin}")
            validated_origins.append(normalized)

        deduplicated: list[str] = []
        seen: set[str] = set()
        for origin in validated_origins:
            key = origin.lower()
            if key not in seen:
                seen.add(key)
                deduplicated.append(origin)

        return deduplicated if deduplicated else None


class EmbedDeploymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    agent_id: UUID
    embed_id: str
    is_active: bool
    allowed_origins: Optional[List[str]]
    token_ttl_seconds: int
    max_concurrent_sessions: int
    room_name_prefix: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RealtimeTokenRequest(BaseModel):
    room_name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=128,
        description="Optional room name. If omitted, server generates one.",
    )
    participant_identity: Optional[str] = Field(
        None,
        min_length=3,
        max_length=128,
        description="Optional participant identity. If omitted, server generates one.",
    )
    participant_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=120,
        description="Display name for the participant.",
    )
    participant_metadata: Optional[str] = Field(
        None,
        max_length=4000,
        description="Optional metadata attached to participant token.",
    )
    participant_attributes: Optional[Dict[str, str]] = Field(
        None,
        description="Optional participant attributes attached to participant token.",
    )
    room_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional room config object. Agent dispatch is always enforced by server.",
    )
    origin_hint: Optional[str] = Field(
        None,
        description="Optional parent origin hint used by iframe embed clients.",
    )

    @field_validator("participant_attributes")
    @classmethod
    def validate_participant_attributes(
        cls, v: Optional[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        if v is None:
            return None

        if len(v) > 20:
            raise ValueError("participant_attributes supports at most 20 entries")

        sanitized: Dict[str, str] = {}
        for key, value in v.items():
            clean_key = str(key).strip()
            clean_value = str(value).strip()
            if not clean_key:
                raise ValueError("participant_attributes keys must be non-empty")
            if len(clean_key) > 64:
                raise ValueError(f"participant_attributes key is too long: {clean_key[:64]}")
            if len(clean_value) > 256:
                raise ValueError(f"participant_attributes value is too long for key: {clean_key}")
            sanitized[clean_key] = clean_value

        return sanitized


class RealtimeTokenResponse(BaseModel):
    server_url: str
    participant_token: str
    room_name: str
    participant_identity: str
    participant_name: str
    expires_at: datetime
    agent_id: UUID
    session_id: UUID
    embed_id: Optional[str] = None


class RealtimeSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    agent_id: UUID
    embed_deployment_id: Optional[UUID]
    room_name: str
    participant_identity: str
    participant_name: Optional[str]
    status: str
    expires_at: Optional[datetime]
    ended_at: Optional[datetime]
    session_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RealtimeSessionEndRequest(BaseModel):
    origin_hint: Optional[str] = Field(
        None,
        description="Optional parent origin hint used by iframe embed clients when ending a session.",
    )
