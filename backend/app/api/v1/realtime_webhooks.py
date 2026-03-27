from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, status, Depends
from sqlalchemy.orm import Session
from livekit import api as livekit_api
from app.core.config import settings
from app.core.database import get_db
from app.models.realtime_session import RealtimeSession

router = APIRouter()


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return auth_header


@router.post("/livekit", status_code=status.HTTP_204_NO_CONTENT)
async def handle_livekit_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LiveKit credentials are not configured for webhook verification.",
        )

    body = (await request.body()).decode("utf-8")
    token = _extract_bearer_token(request)

    try:
        receiver = livekit_api.WebhookReceiver(
            livekit_api.TokenVerifier(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        )
        event = receiver.receive(body, token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature") from exc

    event_name = str(event.event)
    now = datetime.utcnow()

    # Keep status in sync from LiveKit callbacks.
    if event_name in {"participant_left", "participant_disconnected"} and event.participant:
        identity = event.participant.identity
        room_name = event.room.name if event.room else None
        if identity and room_name:
            session = (
                db.query(RealtimeSession)
                .filter(
                    RealtimeSession.room_name == room_name,
                    RealtimeSession.participant_identity == identity,
                    RealtimeSession.status == "active",
                )
                .order_by(RealtimeSession.created_at.desc())
                .first()
            )
            if session:
                session.status = "ended"
                session.ended_at = now
                db.commit()

    if event_name == "room_finished" and event.room:
        room_name = event.room.name
        sessions = (
            db.query(RealtimeSession)
            .filter(
                RealtimeSession.room_name == room_name,
                RealtimeSession.status == "active",
            )
            .all()
        )
        if sessions:
            for session in sessions:
                session.status = "ended"
                session.ended_at = now
            db.commit()

    return None
