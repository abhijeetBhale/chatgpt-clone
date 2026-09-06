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


# --- Personality & Learning Schemas ---

class UserPreferenceRequest(BaseModel):
    tone: Optional[str] = "balanced"  # 'formal', 'casual', 'enthusiastic', 'minimal', 'balanced'
    response_length: Optional[str] = "adaptive"  # 'concise', 'detailed', 'adaptive'
    expertise_level: Optional[str] = "auto"  # 'beginner', 'intermediate', 'expert', 'auto'
    humor_level: Optional[float] = 0.5  # 0.0 to 1.0


class UserPreferenceResponse(BaseModel):
    user_id: str
    tone: str
    response_length: str
    expertise_level: str
    humor_level: float
    feedback_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def to_frontend(self) -> dict:
        return {
            "userId": self.user_id,
            "tone": self.tone,
            "responseLength": self.response_length,
            "expertiseLevel": self.expertise_level,
            "humorLevel": self.humor_level,
            "feedbackCount": self.feedback_count,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


class UserMemoryResponse(BaseModel):
    id: int
    user_id: str
    memory_type: str
    key: str
    value: str
    confidence: float
    source: str
    created_at: datetime
    last_used_at: datetime

    class Config:
        from_attributes = True

    def to_frontend(self) -> dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "memoryType": self.memory_type,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "createdAt": self.created_at.isoformat(),
            "lastUsedAt": self.last_used_at.isoformat(),
        }


class FeedbackAnalyticsResponse(BaseModel):
    id: int
    user_id: Optional[str]
    category: str
    pattern: str
    positive_count: int
    negative_count: int
    last_updated: datetime

    class Config:
        from_attributes = True

    def to_frontend(self) -> dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "category": self.category,
            "pattern": self.pattern,
            "positiveCount": self.positive_count,
            "negativeCount": self.negative_count,
            "lastUpdated": self.last_updated.isoformat(),
        }


class UserSummary(BaseModel):
    user_id: str
    chat_count: int
    message_count: int
    first_seen: datetime
    last_active: datetime

    def to_frontend(self) -> dict:
        return {
            "userId": self.user_id,
            "chatCount": self.chat_count,
            "messageCount": self.message_count,
            "firstSeen": self.first_seen.isoformat(),
            "lastActive": self.last_active.isoformat(),
        }
