from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class RealtimeSession(Base):
    __tablename__ = "realtime_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    embed_deployment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_embed_deployments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    room_name = Column(String, nullable=False, index=True)
    participant_identity = Column(String, nullable=False, index=True)
    participant_name = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    session_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="realtime_sessions")
    agent = relationship("Agent", back_populates="realtime_sessions")
    embed_deployment = relationship("AgentEmbedDeployment", back_populates="sessions")
