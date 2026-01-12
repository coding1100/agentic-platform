from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.models.message import MessageRole


class MessageCreate(BaseModel):
    conversation_id: UUID
    role: MessageRole
    content: str


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

