from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.security import decode_access_token, verify_api_key
from app.models.user import User
from app.models.api_key import ApiKey

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
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


async def get_api_key_user(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    origin: Optional[str] = Header(None),
    db: Session = Depends(get_db)
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
                pass
    
    # Find API key by checking hash
    api_keys = db.query(ApiKey).filter(ApiKey.is_active.is_(True)).all()
    
    matching_key = None
    for key in api_keys:
        if verify_api_key(x_api_key, key.key_hash):
            matching_key = key
            break
    
    if not matching_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # Check expiration
    if matching_key.expires_at and matching_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )
    
    # Validate domain whitelisting
    if not matching_key.is_origin_allowed(request_origin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key is not authorized for origin: {request_origin or 'unknown'}. "
                   f"Allowed origins: {matching_key.allowed_origins or 'all'}",
        )
    
    # Update last used timestamp
    matching_key.last_used_at = datetime.utcnow()
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

