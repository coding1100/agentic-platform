from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from app.schemas.message import MessageResponse


class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: str
    agent_id: UUID
    user_message: Optional[MessageResponse] = None
    assistant_message: Optional[MessageResponse] = None

