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


class EditHistoryEntry(BaseModel):
    message_index: int
    original_text: str
    edited_text: str
    edited_at: datetime


class CreateChatRequest(BaseModel):
    text: str


class UpdateChatRequest(BaseModel):
    question: Optional[str] = None
    answer: str
    img: Optional[str] = None


class MessageRequest(BaseModel):
    question: Optional[str] = None
    img: Optional[str] = None


class FeedbackRequest(BaseModel):
    message_index: int
    feedback_type: str  # "like", "dislike", or "none"


class ShareRequest(BaseModel):
    is_shared: bool


class EditMessageRequest(BaseModel):
    message_index: int
    original_text: str
    edited_text: str


class ChatResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    history: list[HistoryEntry]
    is_shared: bool
    feedback: dict
    edit_history: list[EditHistoryEntry]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def to_frontend(self) -> dict:
        return {
            "_id": str(self.id),
            "userId": self.user_id,
            "history": self.history,
            "isShared": self.is_shared,
            "feedback": self.feedback,
            "editHistory": self.edit_history,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


class UserChatEntry(BaseModel):
    id: uuid.UUID
    title: str
    is_shared: bool
    created_at: datetime

    class Config:
        from_attributes = True

    def to_frontend(self) -> dict:
        return {
            "_id": str(self.id),
            "title": self.title,
            "isShared": self.is_shared,
            "createdAt": self.created_at.isoformat(),
        }
