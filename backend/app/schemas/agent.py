from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, Literal, Dict, Any


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    system_prompt: str = Field(..., min_length=1)
    greeting_message: Optional[str] = Field(None, max_length=2000)
    model: str = Field(default="gemini-2.5-pro")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    interaction_mode: Literal["chat", "avatar_realtime"] = "chat"
    livekit_agent_name: Optional[str] = Field(None, max_length=200)
    avatar_provider: Optional[str] = Field(None, max_length=100)
    avatar_id: Optional[str] = Field(None, max_length=200)
    realtime_config: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_realtime_config(self):
        if self.interaction_mode == "avatar_realtime" and not self.livekit_agent_name:
            raise ValueError("livekit_agent_name is required when interaction_mode is avatar_realtime")
        return self


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    system_prompt: Optional[str] = Field(None, min_length=1)
    greeting_message: Optional[str] = Field(None, max_length=2000)
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    interaction_mode: Optional[Literal["chat", "avatar_realtime"]] = None
    livekit_agent_name: Optional[str] = Field(None, max_length=200)
    avatar_provider: Optional[str] = Field(None, max_length=100)
    avatar_id: Optional[str] = Field(None, max_length=200)
    realtime_config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    system_prompt: str
    greeting_message: Optional[str]
    model: str
    temperature: float
    slug: Optional[str] = None
    category: Optional[str] = None
    is_prebuilt: bool = False
    interaction_mode: Literal["chat", "avatar_realtime"] = "chat"
    livekit_agent_name: Optional[str] = None
    avatar_provider: Optional[str] = None
    avatar_id: Optional[str] = None
    realtime_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

