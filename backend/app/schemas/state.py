from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime


class UserStateUpsert(BaseModel):
    data: Dict[str, Any] = Field(default_factory=dict)


class UserStateResponse(BaseModel):
    namespace: str
    data: Dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
