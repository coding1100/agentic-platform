from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from threading import Lock
from collections import defaultdict
from urllib.parse import urlparse
from dataclasses import dataclass
import hashlib
import json
import logging

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token, verify_api_key
from app.models.user import User
from app.models.api_key import ApiKey

try:
    import redis
except Exception:  # pragma: no cover - optional dependency in some test envs
    redis = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_rate_limit_lock = Lock()
_rate_limit_state = defaultdict(lambda: {"window_start": None, "count": 0})
_auth_cache_lock = Lock()
_auth_cache_state = {}  # cache_key -> (expires_at_utc, payload_dict)
_redis_client = None
_redis_init_attempted = False
logger = logging.getLogger("app.auth")


@dataclass
class CachedApiKeyContext:
    id: UUID
    user_id: UUID
    agent_id: Optional[UUID]
    rate_limit_per_minute: int
    allowed_origins: Optional[list]


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


def _get_redis_client():
    global _redis_client, _redis_init_attempted

    if _redis_client is not None:
        return _redis_client
    if _redis_init_attempted:
        return None

    _redis_init_attempted = True
    if not settings.REDIS_URL or redis is None:
        return None

    try:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=0.2,
            socket_connect_timeout=0.2,
        )
    except Exception:
        _redis_client = None
    return _redis_client


def _fingerprint_api_key(plain_key: str) -> str:
    return hashlib.sha256(plain_key.encode("utf-8")).hexdigest()


def _auth_cache_key(key_id: UUID, key_fp: str) -> str:
    return f"ak_auth:{key_id}:{key_fp}"


def _is_origin_allowed_cached(request_origin: Optional[str], allowed_origins: Optional[list]) -> bool:
    if not allowed_origins or len(allowed_origins) == 0:
        return True
    if not request_origin:
        return True
    normalized_origin = request_origin.rstrip("/").lower()
    for allowed in allowed_origins:
        if normalized_origin == str(allowed).rstrip("/").lower():
            return True
    return False


def _load_cached_api_key(cache_key: str) -> Optional[dict]:
    redis_client = _get_redis_client()
    if redis_client:
        try:
            raw = redis_client.get(cache_key)
            if raw:
                return json.loads(raw)
        except Exception:
            # Gracefully degrade to in-memory cache.
            pass

    with _auth_cache_lock:
        hit = _auth_cache_state.get(cache_key)
        if not hit:
            return None
        expires_at, payload = hit
        if datetime.utcnow() >= expires_at:
            _auth_cache_state.pop(cache_key, None)
            return None
        return payload


def _store_cached_api_key(cache_key: str, payload: dict) -> None:
    ttl = max(1, int(settings.API_KEY_AUTH_CACHE_TTL_SECONDS))
    redis_client = _get_redis_client()
    if redis_client:
        try:
            redis_client.setex(cache_key, ttl, json.dumps(payload))
            return
        except Exception:
            pass

    with _auth_cache_lock:
        _auth_cache_state[cache_key] = (datetime.utcnow() + timedelta(seconds=ttl), payload)


def invalidate_api_key_cache(api_key_id: str) -> None:
    """Invalidate cached auth entries for a specific API key id."""
    if not api_key_id:
        return
    prefix = f"ak_auth:{api_key_id}:"

    with _auth_cache_lock:
        for key in list(_auth_cache_state.keys()):
            if key.startswith(prefix):
                _auth_cache_state.pop(key, None)

    redis_client = _get_redis_client()
    if redis_client:
        try:
            cursor = 0
            pattern = f"{prefix}*"
            while True:
                cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    redis_client.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass


def _enforce_rate_limit(key_id: str, limit: int, now: datetime) -> None:
    # Preferred: distributed rate limit in Redis for multi-instance deployments.
    redis_client = _get_redis_client()
    if redis_client:
        try:
            window_s = max(1, int(settings.API_KEY_RATE_LIMIT_WINDOW_SECONDS))
            bucket = int(now.timestamp()) // window_s
            rl_key = f"ak_rl:{key_id}:{bucket}"

            count = redis_client.incr(rl_key)
            if count == 1:
                redis_client.expire(rl_key, window_s + 2)
            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="API key rate limit exceeded. Please slow down.",
                )
            return
        except HTTPException:
            raise
        except Exception:
            # If Redis has issues, gracefully fall back to local limiter.
            pass

    # Fallback: per-process in-memory limiter.
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

    key_fp = _fingerprint_api_key(x_api_key)
    cached_payload = _load_cached_api_key(_auth_cache_key(key_id, key_fp))

    if cached_payload:
        allowed_origins = cached_payload.get("allowed_origins") or None
        if not _is_origin_allowed_cached(request_origin, allowed_origins):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"API key is not authorized for origin: {request_origin or 'unknown'}. "
                    f"Allowed origins: {allowed_origins or 'all'}"
                ),
            )

        _enforce_rate_limit(
            str(cached_payload["id"]),
            int(cached_payload["rate_limit_per_minute"]),
            now,
        )

        user_id = UUID(cached_payload["user_id"])
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User associated with API key not found",
            )

        api_key_ctx = CachedApiKeyContext(
            id=UUID(cached_payload["id"]),
            user_id=user_id,
            agent_id=UUID(cached_payload["agent_id"]) if cached_payload.get("agent_id") else None,
            rate_limit_per_minute=int(cached_payload["rate_limit_per_minute"]),
            allowed_origins=allowed_origins,
        )
        return user, api_key_ctx

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

    cache_payload = {
        "id": str(matching_key.id),
        "user_id": str(matching_key.user_id),
        "agent_id": str(matching_key.agent_id) if matching_key.agent_id else None,
        "rate_limit_per_minute": int(matching_key.rate_limit_per_minute),
        "allowed_origins": matching_key.allowed_origins or None,
    }
    _store_cached_api_key(_auth_cache_key(key_id, key_fp), cache_payload)

    user = db.query(User).filter(User.id == matching_key.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with API key not found",
        )

    return user, matching_key
