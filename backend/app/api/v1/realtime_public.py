from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.agent import Agent
from app.models.agent_embed_deployment import AgentEmbedDeployment
from app.models.realtime_session import RealtimeSession
from app.schemas.realtime import (
    RealtimeSessionEndRequest,
    RealtimeTokenRequest,
    RealtimeTokenResponse,
)
from app.services.livekit import (
    build_agent_dispatch_room_config,
    generate_participant_identity,
    generate_room_name,
    issue_livekit_participant_token,
)

router = APIRouter()


def _extract_request_origin(request: Request) -> str | None:
    origin = request.headers.get("Origin")
    if origin:
        return origin.rstrip("/")

    referer = request.headers.get("Referer")
    if not referer:
        return None

    try:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    except Exception:
        return None

    return None


def _extract_origin_from_hint(origin_hint: str | None) -> str | None:
    if not origin_hint:
        return None
    try:
        parsed = urlparse(origin_hint)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    except Exception:
        return None
    return None


def _resolve_authorized_origin(
    deployment: AgentEmbedDeployment,
    request: Request,
    origin_hint: str | None,
) -> str | None:
    request_origin = _extract_request_origin(request)
    hinted_origin = _extract_origin_from_hint(origin_hint)

    if origin_hint is not None and hinted_origin is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="origin_hint must be a valid origin value like https://example.com",
        )

    for candidate in [request_origin, hinted_origin]:
        if deployment.is_origin_allowed(candidate):
            return candidate

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            f"Embed deployment is not authorized for origin: {request_origin or hinted_origin or 'unknown'}. "
            f"Allowed origins: {deployment.allowed_origins or 'none configured'}"
        ),
    )


def _validate_realtime_agent(agent: Agent) -> None:
    if agent.interaction_mode != "avatar_realtime":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is not configured for avatar realtime mode",
        )
    if not agent.livekit_agent_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is missing livekit_agent_name for dispatch",
        )


def _expire_stale_sessions(db: Session, deployment_id) -> None:
    now = datetime.utcnow()
    stale_sessions = (
        db.query(RealtimeSession)
        .filter(
            RealtimeSession.embed_deployment_id == deployment_id,
            RealtimeSession.status == "active",
            RealtimeSession.expires_at.isnot(None),
            RealtimeSession.expires_at <= now,
        )
        .all()
    )
    if not stale_sessions:
        return
    for session in stale_sessions:
        session.status = "expired"
        session.ended_at = now
    db.flush()


@router.post(
    "/embed/{embed_id}/token",
    response_model=RealtimeTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_public_embed_token(
    embed_id: str,
    payload: RealtimeTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    deployment = (
        db.query(AgentEmbedDeployment)
        .filter(
            AgentEmbedDeployment.embed_id == embed_id,
            AgentEmbedDeployment.is_active.is_(True),
        )
        .with_for_update()
        .first()
    )
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Embed deployment not found")

    allowed_origin = _resolve_authorized_origin(deployment, request, payload.origin_hint)

    if payload.room_config is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="room_config is not configurable for public embed token endpoint",
        )
    if payload.room_name is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="room_name is not configurable for public embed token endpoint",
        )
    if payload.participant_identity is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="participant_identity is not configurable for public embed token endpoint",
        )
    agent = (
        db.query(Agent)
        .filter(
            Agent.id == deployment.agent_id,
            Agent.is_active.is_(True),
        )
        .first()
    )
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found for embed deployment")

    _validate_realtime_agent(agent)
    _expire_stale_sessions(db, deployment.id)
    active_count = (
        db.query(RealtimeSession)
        .filter(
            RealtimeSession.embed_deployment_id == deployment.id,
            RealtimeSession.status == "active",
        )
        .count()
    )
    if active_count >= deployment.max_concurrent_sessions:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Concurrent session limit reached for this deployment "
                f"({deployment.max_concurrent_sessions})."
            ),
        )

    room_name = generate_room_name(deployment.room_name_prefix, agent.id)
    participant_identity = generate_participant_identity("emb")
    participant_name = payload.participant_name or "candidate"

    try:
        room_config = build_agent_dispatch_room_config(agent)
        issued = issue_livekit_participant_token(
            room_name=room_name,
            participant_identity=participant_identity,
            participant_name=participant_name,
            room_config=room_config,
            ttl_seconds=deployment.token_ttl_seconds,
            participant_metadata=payload.participant_metadata,
            participant_attributes=payload.participant_attributes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    session_record = RealtimeSession(
        user_id=deployment.user_id,
        agent_id=agent.id,
        embed_deployment_id=deployment.id,
        room_name=issued.room_name,
        participant_identity=issued.participant_identity,
        participant_name=issued.participant_name,
        status="active",
        expires_at=issued.expires_at,
        ended_at=None,
        session_metadata={
            "source": "embed",
            "origin": allowed_origin,
            "participant_metadata": payload.participant_metadata,
            "participant_attributes": payload.participant_attributes,
        },
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    return RealtimeTokenResponse(
        server_url=issued.server_url,
        participant_token=issued.participant_token,
        room_name=issued.room_name,
        participant_identity=issued.participant_identity,
        participant_name=issued.participant_name,
        expires_at=issued.expires_at,
        agent_id=agent.id,
        session_id=session_record.id,
        embed_id=deployment.embed_id,
    )


@router.post(
    "/embed/{embed_id}/sessions/{session_id}/end",
    status_code=status.HTTP_204_NO_CONTENT,
)
def end_public_embed_session(
    embed_id: str,
    session_id: UUID,
    request: Request,
    payload: RealtimeSessionEndRequest | None = Body(default=None),
    db: Session = Depends(get_db),
):
    deployment = (
        db.query(AgentEmbedDeployment)
        .filter(AgentEmbedDeployment.embed_id == embed_id)
        .first()
    )
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Embed deployment not found")

    origin_hint = payload.origin_hint if payload else None
    _resolve_authorized_origin(deployment, request, origin_hint)

    session = (
        db.query(RealtimeSession)
        .filter(
            RealtimeSession.id == session_id,
            RealtimeSession.embed_deployment_id == deployment.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Realtime session not found")

    if session.status == "active":
        now = datetime.utcnow()
        session.status = "ended"
        session.ended_at = now
        db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
