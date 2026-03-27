from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import Optional
from app.core.database import Base


class AgentEmbedDeployment(Base):
    __tablename__ = "agent_embed_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    embed_id = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    allowed_origins = Column(JSON, nullable=True)
    token_ttl_seconds = Column(Integer, default=900, nullable=False)
    max_concurrent_sessions = Column(Integer, default=5, nullable=False)
    room_name_prefix = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "agent_id", name="uq_agent_embed_deployments_user_agent"),
    )

    user = relationship("User", back_populates="embed_deployments")
    agent = relationship("Agent", back_populates="embed_deployments")
    sessions = relationship("RealtimeSession", back_populates="embed_deployment")

    def is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check whether the given browser origin is allowed for token issuance."""
        if not self.allowed_origins or len(self.allowed_origins) == 0:
            return True

        if not origin:
            return False

        normalized_origin = origin.rstrip("/").lower()
        return any(
            normalized_origin == str(allowed).rstrip("/").lower()
            for allowed in self.allowed_origins
        )
