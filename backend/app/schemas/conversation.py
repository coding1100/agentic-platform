from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.schemas.message import MessageResponse


class ConversationCreate(BaseModel):
    agent_id: UUID
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    id: UUID
    agent_id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

