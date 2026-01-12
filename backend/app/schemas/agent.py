from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    system_prompt: str = Field(..., min_length=1)
    greeting_message: Optional[str] = Field(None, max_length=2000)
    model: str = Field(default="gemini-2.5-pro")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    system_prompt: Optional[str] = Field(None, min_length=1)
    greeting_message: Optional[str] = Field(None, max_length=2000)
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)


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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

