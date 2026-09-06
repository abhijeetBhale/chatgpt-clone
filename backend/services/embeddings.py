"""Embedding Service - Creates and manages vector embeddings for RAG.

Uses a lightweight approach with sentence-transformers or fallback to
TF-IDF vectors for embedding generation.
"""
from __future__ import annotations

import logging
import hashlib
import json
from typing import Optional
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import ConversationEmbedding, ConversationSummary

log = logging.getLogger("embeddings")

# Simple keyword-based embedding as fallback (no external API needed)
# This creates a sparse vector representation based on word presence
EMBEDDING_DIM = 128  # Reduced dimensionality for efficiency

# Common words to ignore
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'out', 'off', 'over',
    'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
    'so', 'than', 'too', 'very', 'just', 'don', 'now', 'i', 'me', 'my',
    'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
    'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
    'these', 'those', 'am', 'and', 'but', 'if', 'or', 'because', 'while',
    'about', 'up', 'down', 'also', 'much', 'many', 'like', 'even', 'well',
    'get', 'got', 'make', 'made', 'let', 'say', 'said', 'go', 'going',
    'come', 'came', 'take', 'took', 'give', 'gave', 'know', 'knew',
    'think', 'thought', 'see', 'saw', 'want', 'use', 'used', 'find',
    'found', 'tell', 'told', 'ask', 'asked', 'work', 'seem', 'feel',
    'felt', 'try', 'tried', 'leave', 'called', 'need', 'become', 'keep',
    'kept', 'begin', 'began', 'show', 'hear', 'play', 'ran', 'move',
    'live', 'believe', 'bring', 'happen', 'must', 'really', 'already',
    'since', 'long', 'back', 'right', 'still', 'though', 'yet', 'way',
    'thing', 'things', 'something', 'nothing', 'everything', 'anything',
    'one', 'two', 'first', 'new', 'good', 'sure', 'real', 'us', 'yes',
}


def _text_to_embedding(text_content: str) -> list[float]:
    """Convert text to a sparse embedding vector using keyword hashing.
    
    This is a lightweight alternative to neural embeddings that doesn't
    require external APIs or large models.
    """
    # Tokenize and clean
    words = text_content.lower().split()
    words = [w.strip('.,!?;:()[]{}"\'-') for w in words]
    words = [w for w in words if w and len(w) > 2 and w not in STOP_WORDS]
    
    # Create embedding using consistent hashing
    embedding = [0.0] * EMBEDDING_DIM
    
    for word in words:
        # Use hash to deterministically place word in embedding space
        hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = hash_val % EMBEDDING_DIM
        embedding[idx] += 1.0
        
        # Also add to neighboring positions for smoothness
        embedding[(idx + 1) % EMBEDDING_DIM] += 0.5
        embedding[(idx - 1) % EMBEDDING_DIM] += 0.5
    
    # Normalize
    norm = sum(x * x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


class EmbeddingService:
    """Manages vector embeddings for conversation chunks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_embedding(
        self,
        user_id: str,
        chat_id: str,
        text_content: str,
        chunk_type: str,
        metadata: dict = None
    ) -> ConversationEmbedding:
        """Store an embedding for a conversation chunk."""
        embedding = _text_to_embedding(text_content)
        
        record = ConversationEmbedding(
            user_id=user_id,
            chat_id=chat_id,
            chunk_text=text_content[:2000],  # Limit storage
            chunk_type=chunk_type,
            embedding=embedding,
            metadata_json=metadata or {},
        )
        self.db.add(record)
        await self.db.flush()
        
        log.info("Stored embedding for user %s, chat %s, type %s", user_id, chat_id, chunk_type)
        return record

    async def search_similar(
        self,
        user_id: str,
        query_text: str,
        limit: int = 5,
        exclude_chat_id: str = None,
        chunk_types: list[str] = None
    ) -> list[dict]:
        """Search for similar conversation chunks using cosine similarity."""
        query_embedding = _text_to_embedding(query_text)
        
        # Fetch user's embeddings (limit to recent for efficiency)
        query = select(ConversationEmbedding).where(
            ConversationEmbedding.user_id == user_id
        )
        
        if exclude_chat_id:
            query = query.where(ConversationEmbedding.chat_id != exclude_chat_id)
        
        if chunk_types:
            query = query.where(ConversationEmbedding.chunk_type.in_(chunk_types))
        
        query = query.order_by(ConversationEmbedding.created_at.desc()).limit(500)
        
        result = await self.db.execute(query)
        embeddings = list(result.scalars().all())
        
        # Compute similarities
        scored = []
        for emb in embeddings:
            similarity = _cosine_similarity(query_embedding, emb.embedding)
            if similarity > 0.1:  # Minimum threshold
                scored.append({
                    'id': emb.id,
                    'text': emb.chunk_text,
                    'type': emb.chunk_type,
                    'chat_id': emb.chat_id,
                    'similarity': similarity,
                    'metadata': emb.metadata_json,
                    'created_at': emb.created_at.isoformat(),
                })
        
        # Sort by similarity and return top N
        scored.sort(key=lambda x: x['similarity'], reverse=True)
        return scored[:limit]

    async def store_conversation_turn(
        self,
        user_id: str,
        chat_id: str,
        user_message: str,
        ai_response: str
    ) -> None:
        """Store embeddings for a complete conversation turn."""
        # Store user message
        await self.store_embedding(
            user_id=user_id,
            chat_id=chat_id,
            text_content=user_message,
            chunk_type='user_message',
            metadata={'role': 'user'}
        )
        
        # Store AI response
        await self.store_embedding(
            user_id=user_id,
            chat_id=chat_id,
            text_content=ai_response,
            chunk_type='ai_response',
            metadata={'role': 'assistant'}
        )

    async def get_user_embedding_count(self, user_id: str) -> int:
        """Get total number of embeddings for a user."""
        result = await self.db.execute(
            select(ConversationEmbedding.id).where(
                ConversationEmbedding.user_id == user_id
            )
        )
        return len(list(result.scalars().all()))


class SummaryService:
    """Manages conversation summaries for context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_summary(
        self,
        user_id: str,
        chat_id: str,
        messages: list[dict]
    ) -> ConversationSummary:
        """Get existing summary or create a new one."""
        result = await self.db.execute(
            select(ConversationSummary).where(
                ConversationSummary.chat_id == chat_id
            )
        )
        summary = result.scalar_one_or_none()
        
        if not summary:
            summary = ConversationSummary(
                user_id=user_id,
                chat_id=chat_id,
                summary="",
                key_topics=[],
                extracted_patterns={},
                message_count=0,
            )
            self.db.add(summary)
        
        return summary

    async def update_summary(
        self,
        user_id: str,
        chat_id: str,
        messages: list[dict]
    ) -> ConversationSummary:
        """Update conversation summary with new messages."""
        summary = await self.get_or_create_summary(user_id, chat_id, messages)
        
        # Extract key information from messages
        user_msgs = [m for m in messages if m.get('role') == 'user']
        ai_msgs = [m for m in messages if m.get('role') == 'model']
        
        # Simple extractive summary (last 3 exchanges)
        recent_exchanges = []
        for i in range(max(0, len(messages) - 6), len(messages), 2):
            if i < len(messages) - 1:
                user_text = messages[i].get('parts', [{}])[0].get('text', '')[:100]
                ai_text = messages[i + 1].get('parts', [{}])[0].get('text', '')[:100]
                recent_exchanges.append(f"User: {user_text}\nAI: {ai_text}")
        
        summary.summary = "\n\n".join(recent_exchanges[-3:])  # Keep last 3 exchanges
        summary.message_count = len(messages)
        
        # Extract topics (simple keyword extraction)
        all_text = " ".join([m.get('parts', [{}])[0].get('text', '') for m in messages])
        topics = self._extract_topics(all_text)
        summary.key_topics = topics
        
        summary.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        
        return summary

    def _extract_topics(self, text: str) -> list[str]:
        """Extract key topics from text."""
        topic_keywords = {
            'python': ['python', 'django', 'flask', 'fastapi', 'pip'],
            'javascript': ['javascript', 'js', 'react', 'node', 'npm', 'vue', 'angular'],
            'database': ['sql', 'database', 'postgres', 'mysql', 'mongodb', 'redis'],
            'api': ['api', 'rest', 'graphql', 'endpoint', 'http'],
            'devops': ['docker', 'kubernetes', 'aws', 'deploy', 'ci/cd', 'git'],
            'data': ['data', 'analytics', 'machine learning', 'ai', 'model'],
            'web': ['html', 'css', 'frontend', 'backend', 'web'],
            'mobile': ['ios', 'android', 'mobile', 'app'],
        }
        
        text_lower = text.lower()
        found_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                found_topics.append(topic)
        
        return found_topics[:5]  # Top 5 topics


def get_embedding_service(db: AsyncSession) -> EmbeddingService:
    """Get embedding service instance."""
    return EmbeddingService(db)


def get_summary_service(db: AsyncSession) -> SummaryService:
    """Get summary service instance."""
    return SummaryService(db)