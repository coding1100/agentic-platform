from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.database import get_db
from app.core.security import decode_access_token, verify_api_key
from app.models.user import User
from app.models.api_key import ApiKey

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def _extract_api_key_id_from_plain_key(plain_key: str) -> Optional[UUID]:
    """Extract embedded ApiKey ID from the plain key if present.

    New-format keys look like: ak_<uuidhex>_<random>.
    Old-format keys won't match this pattern and will return None.
    """
    try:
        if not plain_key or not plain_key.startswith("ak_"):
            return None
        parts = plain_key.split("_", 2)
        if len(parts) < 3:
            return None
        # parts[1] should be the UUID hex
        return UUID(hex=parts[1])
    except Exception:
        return None


async def get_api_key_user(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    origin: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Get user and API key from API key authentication. Returns (user, api_key).

    Also validates domain whitelisting if configured for the API key.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide it in the X-API-Key header.",
        )

    # Get origin from header (fallback to Referer if Origin not present)
    request_origin = origin
    if not request_origin:
        referer = request.headers.get("Referer")
        if referer:
            # Extract origin from Referer (e.g., "https://example.com/path" -> "https://example.com")
            try:
                from urllib.parse import urlparse

                parsed = urlparse(referer)
                request_origin = f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                # If origin parsing fails, leave request_origin as None and handle below.
                pass

    now = datetime.utcnow()

    # Fast path: try to extract ApiKey ID from the plain key (new-format keys).
    matching_key: Optional[ApiKey] = None
    key_id = _extract_api_key_id_from_plain_key(x_api_key)
    if key_id is not None:
        candidate = (
            db.query(ApiKey)
            .filter(
                ApiKey.id == key_id,
                ApiKey.is_active.is_(True),
                (ApiKey.expires_at.is_(None) | (ApiKey.expires_at >= now)),
            )
            .first()
        )
        if candidate and verify_api_key(x_api_key, candidate.key_hash):
            matching_key = candidate

    # Fallback path: legacy keys without embedded ID – O(n) scan over active keys.
    if matching_key is None:
        api_keys = (
            db.query(ApiKey)
            .filter(
                ApiKey.is_active.is_(True),
                (ApiKey.expires_at.is_(None) | (ApiKey.expires_at >= now)),
            )
            .all()
        )

        for key in api_keys:
            if verify_api_key(x_api_key, key.key_hash):
                matching_key = key
                break

    if not matching_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Validate domain whitelisting
    if not matching_key.is_origin_allowed(request_origin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"API key is not authorized for origin: {request_origin or 'unknown'}. "
                f"Allowed origins: {matching_key.allowed_origins or 'all'}"
            ),
        )

    # Update last used timestamp
    matching_key.last_used_at = now
    matching_key.total_requests += 1
    db.commit()

    # Get user
    user = db.query(User).filter(User.id == matching_key.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with API key not found",
        )

    return user, matching_key
 
