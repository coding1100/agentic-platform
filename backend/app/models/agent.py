from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    system_prompt = Column(String, nullable=False)
    greeting_message = Column(String, nullable=True)  # Optional greeting message shown when conversation starts
    model = Column(String, default="gemini-2.5-pro", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    slug = Column(String, unique=True, nullable=True)
    category = Column(String, nullable=True)
    is_prebuilt = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    interaction_mode = Column(String, default="chat", nullable=False)
    livekit_agent_name = Column(String, nullable=True)
    avatar_provider = Column(String, nullable=True)
    avatar_id = Column(String, nullable=True)
    realtime_config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="agents")
    conversations = relationship("Conversation", back_populates="agent", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="agent", cascade="all, delete-orphan")
    embed_deployments = relationship("AgentEmbedDeployment", back_populates="agent", cascade="all, delete-orphan")
    realtime_sessions = relationship("RealtimeSession", back_populates="agent", cascade="all, delete-orphan")
