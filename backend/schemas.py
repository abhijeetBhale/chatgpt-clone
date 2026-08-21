import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HistoryPart(BaseModel):
    text: str


class HistoryEntry(BaseModel):
    role: str
    parts: list[HistoryPart]
    img: Optional[str] = None


class CreateChatRequest(BaseModel):
    text: str


class UpdateChatRequest(BaseModel):
    question: Optional[str] = None
    answer: str
    img: Optional[str] = None


class MessageRequest(BaseModel):
    question: Optional[str] = None
    img: Optional[str] = None


class ChatResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    history: list[HistoryEntry]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def to_frontend(self) -> dict:
        return {
            "_id": str(self.id),
            "userId": self.user_id,
            "history": self.history,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


class UserChatEntry(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

    def to_frontend(self) -> dict:
        return {
            "_id": str(self.id),
            "title": self.title,
            "createdAt": self.created_at.isoformat(),
        }
