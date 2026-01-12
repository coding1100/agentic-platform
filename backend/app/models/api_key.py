from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import List, Optional
from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True, index=True)  # Nullable: null = universal key for all agents
    key_hash = Column(String, unique=True, nullable=False, index=True)  # Hashed API key
    name = Column(String, nullable=False)  # User-friendly name for the key
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Rate limiting and usage tracking
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)  # Requests per minute
    total_requests = Column(Integer, default=0, nullable=False)  # Total requests made
    
    # Domain whitelisting (null or empty list = allow all origins)
    allowed_origins = Column(JSON, nullable=True)  # List of allowed origins, e.g., ["https://example.com", "https://app.example.com"]
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    agent = relationship("Agent", back_populates="api_keys")
    
    def is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if the given origin is allowed for this API key."""
        # If no whitelist is set (null or empty), allow all origins
        if not self.allowed_origins or len(self.allowed_origins) == 0:
            return True
        
        # If no origin header is provided, reject (for security)
        if not origin:
            return False
        
        # Normalize origin (remove trailing slash, convert to lowercase for comparison)
        normalized_origin = origin.rstrip('/').lower()
        
        # Check if origin matches any allowed origin
        for allowed in self.allowed_origins:
            normalized_allowed = allowed.rstrip('/').lower()
            if normalized_origin == normalized_allowed:
                return True
        
        return False

