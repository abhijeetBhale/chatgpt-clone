"""Memory Manager - Cross-session memory with privacy controls.

This module manages user memories that persist across conversations:
- Expertise tracking
- Preference learning
- Style patterns
- Topic knowledge

Users have full control over their memories (view, delete, export).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserMemory

log = logging.getLogger("memory")

# Memory types that are safe to persist
SAFE_MEMORY_TYPES = {
    "expertise",
    "preference",
    "style_pattern",
    "topic_expertise",
}

# Memory types that should NOT be persisted (too sensitive)
RESTRICTED_MEMORY_TYPES = {
    "personal_info",
    "private_context",
    "conversation_content",
}

# Default memory expiration (90 days)
DEFAULT_MEMORY_TTL_DAYS = 90


class MemoryType(str, Enum):
    EXPERTISE = "expertise"
    PREFERENCE = "preference"
    STYLE_PATTERN = "style_pattern"
    TOPIC_EXPERTISE = "topic_expertise"


class MemoryManager:
    """Manages cross-session user memories with privacy controls."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        include_expired: bool = False
    ) -> list[UserMemory]:
        """Get memories for a user.
        
        Args:
            user_id: The user's ID
            memory_type: Optional filter by memory type
            include_expired: Whether to include expired memories
            
        Returns:
            List of UserMemory objects
        """
        query = select(UserMemory).where(UserMemory.user_id == user_id)
        
        if memory_type:
            query = query.where(UserMemory.memory_type == memory_type)
        
        if not include_expired:
            query = query.where(
                (UserMemory.expires_at.is_(None)) | 
                (UserMemory.expires_at > datetime.now(timezone.utc))
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_memory(
        self,
        user_id: str,
        memory_type: str,
        key: str,
        value: str,
        confidence: float = 0.5,
        source: str = "inferred",
        ttl_days: Optional[int] = None
    ) -> Optional[UserMemory]:
        """Add or update a memory for a user.
        
        Args:
            user_id: The user's ID
            memory_type: Type of memory (expertise, preference, style_pattern, etc.)
            key: Memory key (e.g., 'python', 'prefers_code_examples')
            value: Memory value
            confidence: Confidence level (0.0 to 1.0)
            source: Source of memory (feedback, explicit, inferred)
            ttl_days: Time to live in days (None for default)
            
        Returns:
            Created/updated UserMemory or None if restricted type
        """
        # Validate memory type
        if memory_type in RESTRICTED_MEMORY_TYPES:
            log.warning("Attempted to store restricted memory type: %s", memory_type)
            return None
        
        if memory_type not in SAFE_MEMORY_TYPES:
            log.warning("Unknown memory type: %s, storing as generic", memory_type)
        
        # Check if memory already exists
        result = await self.db.execute(
            select(UserMemory).where(
                UserMemory.user_id == user_id,
                UserMemory.memory_type == memory_type,
                UserMemory.key == key
            )
        )
        existing = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=ttl_days or DEFAULT_MEMORY_TTL_DAYS)
        
        if existing:
            # Update existing memory
            existing.value = value
            existing.confidence = max(existing.confidence, confidence)
            existing.source = source
            existing.last_used_at = now
            existing.expires_at = expires_at
            await self.db.flush()
            log.info("Updated memory for user %s: %s=%s", user_id, key, value)
            return existing
        else:
            # Create new memory
            new_memory = UserMemory(
                user_id=user_id,
                memory_type=memory_type,
                key=key,
                value=value,
                confidence=confidence,
                source=source,
                created_at=now,
                last_used_at=now,
                expires_at=expires_at,
            )
            self.db.add(new_memory)
            await self.db.flush()
            log.info("Created memory for user %s: %s=%s", user_id, key, value)
            return new_memory

    async def delete_memory(self, user_id: str, memory_id: int) -> bool:
        """Delete a specific memory.
        
        Args:
            user_id: The user's ID (for security verification)
            memory_id: The memory ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(UserMemory).where(
                UserMemory.id == memory_id,
                UserMemory.user_id == user_id
            )
        )
        memory = result.scalar_one_or_none()
        
        if not memory:
            return False
        
        await self.db.delete(memory)
        await self.db.flush()
        
        log.info("Deleted memory %d for user %s", memory_id, user_id)
        return True

    async def delete_all_memories(self, user_id: str) -> int:
        """Delete all memories for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Number of memories deleted
        """
        result = await self.db.execute(
            delete(UserMemory).where(UserMemory.user_id == user_id)
        )
        deleted_count = result.rowcount
        await self.db.flush()
        
        log.info("Deleted all %d memories for user %s", deleted_count, user_id)
        return deleted_count

    async def export_user_data(self, user_id: str) -> dict:
        """Export all user data for GDPR compliance.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with all user data
        """
        memories = await self.get_user_memories(user_id, include_expired=True)
        
        return {
            "user_id": user_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "memories": [
                {
                    "id": m.id,
                    "type": m.memory_type,
                    "key": m.key,
                    "value": m.value,
                    "confidence": m.confidence,
                    "source": m.source,
                    "created_at": m.created_at.isoformat(),
                    "last_used_at": m.last_used_at.isoformat(),
                    "expires_at": m.expires_at.isoformat() if m.expires_at else None,
                }
                for m in memories
            ],
            "total_memories": len(memories),
        }

    async def touch_memory(self, memory_id: int) -> bool:
        """Update the last_used_at timestamp for a memory.
        
        Args:
            memory_id: The memory ID to touch
            
        Returns:
            True if updated, False if not found
        """
        result = await self.db.execute(
            select(UserMemory).where(UserMemory.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        
        if not memory:
            return False
        
        memory.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def cleanup_expired_memories(self) -> int:
        """Remove expired memories. Can be run as a scheduled task.
        
        Returns:
            Number of memories cleaned up
        """
        result = await self.db.execute(
            delete(UserMemory).where(
                UserMemory.expires_at < datetime.now(timezone.utc)
            )
        )
        deleted_count = result.rowcount
        await self.db.flush()
        
        if deleted_count > 0:
            log.info("Cleaned up %d expired memories", deleted_count)
        
        return deleted_count

    async def get_relevant_memories(
        self,
        user_id: str,
        context_keywords: list[str],
        limit: int = 10
    ) -> list[UserMemory]:
        """Get memories relevant to the current context.
        
        Args:
            user_id: The user's ID
            context_keywords: Keywords from the current conversation
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant UserMemory objects, sorted by relevance
        """
        all_memories = await self.get_user_memories(user_id)
        
        if not all_memories:
            return []
        
        # Score memories based on relevance
        scored_memories = []
        for memory in all_memories:
            score = 0
            
            # Direct keyword match
            for keyword in context_keywords:
                if keyword.lower() in memory.key.lower():
                    score += 2
                if keyword.lower() in memory.value.lower():
                    score += 1
            
            # Boost confidence
            score += memory.confidence
            
            # Boost recently used
            if memory.last_used_at:
                days_since_use = (datetime.now(timezone.utc) - memory.last_used_at).days
                if days_since_use < 7:
                    score += 1
                elif days_since_use < 30:
                    score += 0.5
            
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by score and return top N
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in scored_memories[:limit]]


def get_memory_manager(db: AsyncSession) -> MemoryManager:
    """Get or create a MemoryManager instance."""
    return MemoryManager(db)