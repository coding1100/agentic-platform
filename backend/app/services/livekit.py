import json
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID
from google.protobuf.json_format import ParseDict
from livekit import api as livekit_api
from app.core.config import settings
from app.models.agent import Agent

SAFE_TOKEN_RE = re.compile(r"[^a-zA-Z0-9_-]+")
MAX_AGENT_METADATA_INSTRUCTIONS_CHARS = 4000


@dataclass
class IssuedLiveKitToken:
    participant_token: str
    expires_at: datetime
    room_name: str
    participant_identity: str
    participant_name: str
    server_url: str


def ensure_livekit_is_configured() -> None:
    """Validate required LiveKit credentials exist in environment config."""
    if not settings.LIVEKIT_URL or not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise ValueError(
            "LiveKit is not configured. Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET."
        )


def generate_embed_id() -> str:
    return f"emb_{secrets.token_urlsafe(16).rstrip('=')}"


def normalize_room_component(value: Optional[str], fallback: str) -> str:
    raw = (value or fallback).strip().lower()
    normalized = SAFE_TOKEN_RE.sub("-", raw).strip("-")
    if not normalized:
        normalized = fallback
    return normalized[:64]


def generate_room_name(prefix: Optional[str], agent_id: UUID) -> str:
    cleaned_prefix = normalize_room_component(prefix, settings.LIVEKIT_DEFAULT_ROOM_PREFIX)
    suffix = secrets.token_hex(6)
    return f"{cleaned_prefix}-{str(agent_id).split('-')[0]}-{suffix}"


def generate_participant_identity(prefix: str = "participant") -> str:
    cleaned_prefix = normalize_room_component(prefix, "participant")
    return f"{cleaned_prefix}-{secrets.token_hex(6)}"


def _build_dispatch_metadata(agent: Agent) -> str:
    realtime_config = agent.realtime_config if isinstance(agent.realtime_config, dict) else None
    instructions = (agent.system_prompt or "").strip()
    if instructions:
        instructions = instructions[:MAX_AGENT_METADATA_INSTRUCTIONS_CHARS]

    metadata: Dict[str, Any] = {
        "agent_id": str(agent.id),
        "agent_name": agent.name,
        "avatar_provider": agent.avatar_provider,
        "avatar_id": agent.avatar_id,
        "instructions": instructions or None,
        "realtime_config": realtime_config,
    }
    compact_metadata = {key: value for key, value in metadata.items() if value is not None}

    try:
        return json.dumps(compact_metadata)
    except TypeError as exc:
        raise ValueError("Agent realtime_config must be JSON-serializable") from exc


def build_agent_dispatch_room_config(
    agent: Agent,
    incoming_room_config: Optional[Dict[str, Any]] = None,
) -> livekit_api.RoomConfiguration:
    if incoming_room_config:
        try:
            room_config = ParseDict(incoming_room_config, livekit_api.RoomConfiguration())
        except Exception as exc:
            raise ValueError("Invalid room_config payload") from exc
    else:
        room_config = livekit_api.RoomConfiguration()

    room_config.ClearField("agents")
    dispatch = livekit_api.RoomAgentDispatch(
        agent_name=agent.livekit_agent_name or "",
        metadata=_build_dispatch_metadata(agent),
    )
    room_config.agents.append(dispatch)
    return room_config


def issue_livekit_participant_token(
    room_name: str,
    participant_identity: str,
    participant_name: str,
    room_config: livekit_api.RoomConfiguration,
    ttl_seconds: int,
    participant_metadata: Optional[str] = None,
    participant_attributes: Optional[Dict[str, str]] = None,
) -> IssuedLiveKitToken:
    ensure_livekit_is_configured()
    ttl_seconds = max(60, min(3600, int(ttl_seconds)))
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    token = (
        livekit_api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(participant_identity)
        .with_name(participant_name)
        .with_grants(
            livekit_api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(room_config)
        .with_ttl(timedelta(seconds=ttl_seconds))
    )

    if participant_metadata:
        token = token.with_metadata(participant_metadata)

    if participant_attributes:
        token = token.with_attributes(participant_attributes)

    return IssuedLiveKitToken(
        participant_token=token.to_jwt(),
        expires_at=expires_at,
        room_name=room_name,
        participant_identity=participant_identity,
        participant_name=participant_name,
        server_url=settings.LIVEKIT_URL,
    )
