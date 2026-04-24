from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from threading import Lock
from collections import defaultdict
from urllib.parse import urlparse
from app.core.database import get_db
from app.core.security import decode_access_token, verify_api_key
from app.models.user import User
from app.models.api_key import ApiKey

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_rate_limit_lock = Lock()
_rate_limit_state = defaultdict(lambda: {"window_start": None, "count": 0})


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_raw: str = payload.get("sub")
    if user_id_raw is None:
        raise credentials_exception

    try:
        user_id = UUID(str(user_id_raw))
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def _extract_api_key_id_from_plain_key(plain_key: str) -> Optional[UUID]:
    """Extract embedded ApiKey ID from key format ak_<uuidhex>_<random>."""
    try:
        if not plain_key or not plain_key.startswith("ak_"):
            return None
        parts = plain_key.split("_", 2)
        if len(parts) < 3:
            return None
        return UUID(hex=parts[1])
    except Exception:
        return None


def _extract_request_origin(request: Request, origin_header: Optional[str]) -> Optional[str]:
    if origin_header:
        return origin_header
    referer = request.headers.get("Referer")
    if not referer:
        return None
    try:
        parsed = urlparse(referer)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return None


def _enforce_rate_limit(key_id: str, limit: int, now: datetime) -> None:
    with _rate_limit_lock:
        state = _rate_limit_state[key_id]
        window_start = state["window_start"]
        if not window_start or now - window_start >= timedelta(minutes=1):
            state["window_start"] = now
            state["count"] = 1
            return
        if state["count"] >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API key rate limit exceeded. Please slow down.",
            )
        state["count"] += 1


async def get_api_key_user(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    origin: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Validate API key and return (user, api_key)."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide it in the X-API-Key header.",
        )

    now = datetime.utcnow()
    request_origin = _extract_request_origin(request, origin)

    key_id = _extract_api_key_id_from_plain_key(x_api_key)
    if key_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Legacy API key format is no longer supported. Rotate and use a new API key.",
        )

    matching_key = (
        db.query(ApiKey)
        .filter(
            ApiKey.id == key_id,
            ApiKey.is_active.is_(True),
            (ApiKey.expires_at.is_(None) | (ApiKey.expires_at >= now)),
        )
        .first()
    )

    if not matching_key or not verify_api_key(x_api_key, matching_key.key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not matching_key.is_origin_allowed(request_origin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"API key is not authorized for origin: {request_origin or 'unknown'}. "
                f"Allowed origins: {matching_key.allowed_origins or 'all'}"
            ),
        )

    _enforce_rate_limit(str(matching_key.id), matching_key.rate_limit_per_minute, now)

    user = db.query(User).filter(User.id == matching_key.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with API key not found",
        )

    return user, matching_key
