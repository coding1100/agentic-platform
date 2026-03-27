from datetime import datetime
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.agent import Agent
from app.models.agent_embed_deployment import AgentEmbedDeployment
from app.models.realtime_session import RealtimeSession
from app.models.user import User
from app.schemas.realtime import (
    EmbedDeploymentResponse,
    EmbedDeploymentUpsert,
    RealtimeSessionResponse,
    RealtimeTokenRequest,
    RealtimeTokenResponse,
)
from app.services.livekit import (
    build_agent_dispatch_room_config,
    generate_embed_id,
    generate_participant_identity,
    generate_room_name,
    issue_livekit_participant_token,
    normalize_room_component,
)

router = APIRouter()


def _get_agent_with_access(db: Session, current_user: User, agent_id: UUID) -> Agent:
    agent = (
        db.query(Agent)
        .filter(
            Agent.id == agent_id,
            (
                (Agent.user_id == current_user.id)
                | (Agent.is_prebuilt.is_(True) & Agent.is_active.is_(True))
            ),
        )
        .first()
    )
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


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


def _get_active_deployment_for_update(
    db: Session,
    user_id: UUID,
    agent_id: UUID,
) -> Optional[AgentEmbedDeployment]:
    return (
        db.query(AgentEmbedDeployment)
        .filter(
            AgentEmbedDeployment.user_id == user_id,
            AgentEmbedDeployment.agent_id == agent_id,
            AgentEmbedDeployment.is_active.is_(True),
        )
        .with_for_update()
        .first()
    )


def _expire_stale_sessions(db: Session, deployment_id: Optional[UUID] = None) -> None:
    now = datetime.utcnow()
    query = db.query(RealtimeSession).filter(
        RealtimeSession.status == "active",
        RealtimeSession.expires_at.isnot(None),
        RealtimeSession.expires_at <= now,
    )
    if deployment_id is not None:
        query = query.filter(RealtimeSession.embed_deployment_id == deployment_id)

    stale_sessions = query.all()
    if not stale_sessions:
        return

    for session in stale_sessions:
        session.status = "expired"
        session.ended_at = now
    db.flush()


@router.put("/agents/{agent_id}/embed", response_model=EmbedDeploymentResponse)
def upsert_embed_deployment(
    agent_id: UUID,
    payload: EmbedDeploymentUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = _get_agent_with_access(db, current_user, agent_id)
    _validate_realtime_agent(agent)

    deployment = (
        db.query(AgentEmbedDeployment)
        .filter(
            AgentEmbedDeployment.user_id == current_user.id,
            AgentEmbedDeployment.agent_id == agent_id,
        )
        .first()
    )

    if not deployment:
        deployment = AgentEmbedDeployment(
            user_id=current_user.id,
            agent_id=agent_id,
            embed_id=generate_embed_id(),
            is_active=payload.is_active,
            allowed_origins=payload.allowed_origins,
            token_ttl_seconds=payload.token_ttl_seconds or settings.LIVEKIT_DEFAULT_TOKEN_TTL_SECONDS,
            max_concurrent_sessions=payload.max_concurrent_sessions or 5,
            room_name_prefix=payload.room_name_prefix,
        )
        db.add(deployment)
    else:
        deployment.is_active = payload.is_active
        deployment.allowed_origins = payload.allowed_origins
        if payload.token_ttl_seconds is not None:
            deployment.token_ttl_seconds = payload.token_ttl_seconds
        if payload.max_concurrent_sessions is not None:
            deployment.max_concurrent_sessions = payload.max_concurrent_sessions
        if payload.room_name_prefix is not None:
            deployment.room_name_prefix = payload.room_name_prefix

    db.commit()
    db.refresh(deployment)
    return deployment


@router.get("/agents/{agent_id}/embed", response_model=EmbedDeploymentResponse)
def get_embed_deployment(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_agent_with_access(db, current_user, agent_id)
    deployment = (
        db.query(AgentEmbedDeployment)
        .filter(
            AgentEmbedDeployment.user_id == current_user.id,
            AgentEmbedDeployment.agent_id == agent_id,
        )
        .first()
    )
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Embed deployment not found")
    return deployment


@router.get("/agents/{agent_id}/sessions", response_model=List[RealtimeSessionResponse])
def list_realtime_sessions(
    agent_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_agent_with_access(db, current_user, agent_id)
    safe_limit = max(1, min(limit, 200))

    sessions = (
        db.query(RealtimeSession)
        .filter(
            RealtimeSession.user_id == current_user.id,
            RealtimeSession.agent_id == agent_id,
        )
        .order_by(RealtimeSession.created_at.desc())
        .limit(safe_limit)
        .all()
    )
    return sessions


@router.post("/sessions/{session_id}/end", response_model=RealtimeSessionResponse)
def end_realtime_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(RealtimeSession)
        .filter(
            RealtimeSession.id == session_id,
            RealtimeSession.user_id == current_user.id,
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
        db.refresh(session)

    return session


@router.post(
    "/agents/{agent_id}/token",
    response_model=RealtimeTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_realtime_token_for_agent(
    agent_id: UUID,
    payload: RealtimeTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    agent = _get_agent_with_access(db, current_user, agent_id)
    _validate_realtime_agent(agent)

    deployment = _get_active_deployment_for_update(db, current_user.id, agent_id)

    if deployment:
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

    if payload.room_name:
        room_name = normalize_room_component(payload.room_name, "avatar-room")
    else:
        room_name = generate_room_name(
            deployment.room_name_prefix if deployment else None,
            agent.id,
        )

    participant_identity = (
        normalize_room_component(payload.participant_identity, "participant")
        if payload.participant_identity
        else generate_participant_identity("usr")
    )
    participant_name = payload.participant_name or current_user.email.split("@")[0]
    ttl_seconds = deployment.token_ttl_seconds if deployment else settings.LIVEKIT_DEFAULT_TOKEN_TTL_SECONDS

    try:
        room_config = build_agent_dispatch_room_config(agent, payload.room_config)
        issued = issue_livekit_participant_token(
            room_name=room_name,
            participant_identity=participant_identity,
            participant_name=participant_name,
            room_config=room_config,
            ttl_seconds=ttl_seconds,
            participant_metadata=payload.participant_metadata,
            participant_attributes=payload.participant_attributes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    session_record = RealtimeSession(
        user_id=current_user.id,
        agent_id=agent.id,
        embed_deployment_id=deployment.id if deployment else None,
        room_name=issued.room_name,
        participant_identity=issued.participant_identity,
        participant_name=issued.participant_name,
        status="active",
        expires_at=issued.expires_at,
        ended_at=None,
        session_metadata={
            "source": "dashboard",
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
        embed_id=deployment.embed_id if deployment else None,
    )
