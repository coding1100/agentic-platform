from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)  # Agent-specific
    key_hash = Column(String, unique=True, nullable=False, index=True)  # Hashed API key
    name = Column(String, nullable=False)  # User-friendly name for the key
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Rate limiting and usage tracking
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)  # Requests per minute
    total_requests = Column(Integer, default=0, nullable=False)  # Total requests made
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    agent = relationship("Agent", back_populates="api_keys")

