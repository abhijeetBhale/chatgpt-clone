import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feedback: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    edit_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user_chat_entries: Mapped[list["UserChat"]] = relationship("UserChat", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_chats_user_id", "user_id"),
    )


class UserChat(Base):
    __tablename__ = "user_chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    chat: Mapped["Chat"] = relationship("Chat", back_populates="user_chat_entries")

    __table_args__ = (
        Index("idx_user_chats_user_id", "user_id"),
    )


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    tone: Mapped[str] = mapped_column(String(32), nullable=False, default="balanced")
    response_length: Mapped[str] = mapped_column(String(32), nullable=False, default="adaptive")
    expertise_level: Mapped[str] = mapped_column(String(32), nullable=False, default="auto")
    humor_level: Mapped[float] = mapped_column(nullable=False, default=0.5)
    feedback_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_adapted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_user_preferences_user_id", "user_id"),
    )


class UserMemory(Base):
    __tablename__ = "user_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    memory_type: Mapped[str] = mapped_column(String(32), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.5)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="inferred")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_user_memory_user_id", "user_id"),
        Index("idx_user_memory_type_key", "user_id", "memory_type", "key", unique=True),
    )


class FeedbackAnalytics(Base):
    __tablename__ = "feedback_analytics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False, default="")
    positive_count: Mapped[int] = mapped_column(nullable=False, default=0)
    negative_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_feedback_analytics_user_category", "user_id", "category"),
    )


class ConversationEmbedding(Base):
    """Stores vector embeddings of conversation chunks for RAG retrieval."""
    __tablename__ = "conversation_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    chat_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 'user_message', 'ai_response', 'summary'
    embedding: Mapped[list] = mapped_column(JSONB, nullable=False)  # Will store vector as JSON array
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_embedding_user_id", "user_id"),
        Index("idx_embedding_chat_id", "chat_id"),
    )


class ConversationSummary(Base):
    """Stores auto-generated summaries of conversations for context."""
    __tablename__ = "conversation_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    chat_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_topics: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    extracted_patterns: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    message_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_summary_user_id", "user_id"),
    )
