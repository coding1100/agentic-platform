from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings


def _safe_check(plain_text: str, hashed_text: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_text.encode("utf-8"),
            hashed_text.encode("utf-8"),
        )
    except Exception:
        return False


def _safe_hash(plain_text: str) -> str:
    return bcrypt.hashpw(
        plain_text.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return _safe_check(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return _safe_hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return _safe_hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return _safe_check(plain_key, hashed_key)


def generate_api_key() -> str:
    """Generate a new API key."""
    import secrets
    return f"ak_{secrets.token_urlsafe(32)}"
