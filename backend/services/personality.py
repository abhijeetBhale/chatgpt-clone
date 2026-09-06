"""Personality Engine - Dynamic prompt construction based on user preferences and learning.

This module builds contextual system prompts that adapt to:
- User's preferred tone and response style
- Detected expertise level
- Feedback-derived patterns
- Conversation context
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserPreference, UserMemory, FeedbackAnalytics

log = logging.getLogger("personality")

# Tone descriptions for prompt construction
TONE_DESCRIPTIONS = {
    "formal": "Professional and structured. Use complete sentences, avoid slang, maintain a business-appropriate tone.",
    "casual": "Friendly and relaxed. Use natural conversational language, contractions, and a warm tone.",
    "enthusiastic": "Energetic and positive. Show excitement about topics, use exclamations appropriately, and maintain high energy.",
    "minimal": "Ultra-concise and direct. Get straight to the point with minimal preamble. Use bullet points and short answers.",
    "balanced": "Adaptive and natural. Match the user's energy while staying helpful and clear.",
}

HUMOR_DESCRIPTIONS = {
    0.0: "Completely serious and professional. No humor.",
    0.3: "Occasional light wit when appropriate. Subtle humor only.",
    0.5: "Moderate humor. Friendly and approachable with occasional jokes.",
    0.7: "Witty and playful. Enjoy light banter while staying helpful.",
    1.0: "Maximum personality. Frequent humor, pop culture references, and entertaining responses.",
}

EXPERTISE_DESCRIPTIONS = {
    "beginner": "Explain concepts clearly, avoid jargon, provide context for technical terms, be patient and encouraging.",
    "intermediate": "Balance explanation with efficiency. Provide some technical detail but explain complex parts.",
    "expert": "Use technical language freely, skip basic explanations, focus on advanced concepts and edge cases.",
    "auto": "Adapt to the user's demonstrated knowledge level. Start moderate and adjust based on their questions.",
}


class PersonalityEngine:
    """Builds dynamic system prompts based on user preferences and learned patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_preferences(self, user_id: str) -> UserPreference:
        """Get or create user preferences."""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            prefs = UserPreference(user_id=user_id)
            self.db.add(prefs)
            await self.db.flush()
            log.info("Created default preferences for user %s", user_id)
        
        return prefs

    async def update_user_preferences(self, user_id: str, updates: dict) -> UserPreference:
        """Update user preferences with provided values."""
        prefs = await self.get_user_preferences(user_id)
        
        for key, value in updates.items():
            if hasattr(prefs, key) and value is not None:
                setattr(prefs, key, value)
        
        prefs.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        
        log.info("Updated preferences for user %s: %s", user_id, updates)
        return prefs

    async def get_user_memories(self, user_id: str, memory_type: Optional[str] = None) -> list[UserMemory]:
        """Get active memories for a user."""
        query = select(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.expires_at > datetime.now(timezone.utc) 
        )
        if memory_type:
            query = query.where(UserMemory.memory_type == memory_type)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_feedback_patterns(self, user_id: str) -> list[FeedbackAnalytics]:
        """Get learned feedback patterns for a user (and global patterns)."""
        result = await self.db.execute(
            select(FeedbackAnalytics).where(
                (FeedbackAnalytics.user_id == user_id) | (FeedbackAnalytics.user_id.is_(None))
            ).order_by(FeedbackAnalytics.positive_count.desc())
        )
        return list(result.scalars().all())

    def _detect_topic(self, conversation_history: list[dict]) -> str:
        """Detect the primary topic of the conversation."""
        if not conversation_history:
            return "general"
        
        # Get the last user message for context
        recent_messages = [m for m in conversation_history[-6:] if m.get("role") == "user"]
        if not recent_messages:
            return "general"
        
        last_message = recent_messages[-1].get("content", "").lower()
        
        # Topic detection keywords
        topic_keywords = {
            "coding": ["code", "function", "class", "bug", "error", "programming", "python", "javascript", "api", "database", "sql", "html", "css", "react", "node"],
            "writing": ["write", "essay", "story", "article", "blog", "content", "creative", "fiction", "narrative"],
            "analysis": ["analyze", "data", "chart", "graph", "statistics", "metrics", "report", "research"],
            "math": ["calculate", "equation", "formula", "math", "number", "sum", "average", "probability"],
            "business": ["business", "marketing", "strategy", "revenue", "customer", "sales", "startup", "pitch"],
            "creative": ["design", "creative", "art", "image", "logo", "ui", "ux", "mockup", "wireframe"],
        }
        
        scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for kw in keywords if kw in last_message)
            if score > 0:
                scores[topic] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "general"

    def _estimate_expertise_from_context(self, conversation_history: list[dict], memories: list[UserMemory]) -> str:
        """Estimate user expertise from conversation context and memories."""
        # Check explicit expertise memories
        expertise_memories = [m for m in memories if m.memory_type == "expertise"]
        if expertise_memories:
            # Return highest confidence expertise level
            expertise_memories.sort(key=lambda m: m.confidence, reverse=True)
            return expertise_memories[0].value
        
        # Infer from conversation patterns
        if not conversation_history:
            return "intermediate"
        
        user_messages = [m for m in conversation_history if m.get("role") == "user"]
        if not user_messages:
            return "intermediate"
        
        # Analyze message complexity
        technical_indicators = 0
        beginner_indicators = 0
        
        for msg in user_messages[-5:]:  # Last 5 messages
            content = msg.get("content", "").lower()
            
            # Technical indicators
            technical_terms = ["api", "async", "callback", "middleware", "database", "schema", "endpoint", "authentication"]
            if any(term in content for term in technical_terms):
                technical_indicators += 1
            
            # Beginner indicators
            beginner_phrases = ["how do i", "what is", "can you explain", "i'm new to", "beginner"]
            if any(phrase in content for phrase in beginner_phrases):
                beginner_indicators += 1
        
        if technical_indicators > beginner_indicators:
            return "expert"
        elif beginner_indicators > technical_indicators:
            return "beginner"
        return "intermediate"

    def _get_behavioral_guidelines(self, prefs: UserPreference, topic: str, expertise: str) -> str:
        """Generate behavioral guidelines based on preferences and context."""
        guidelines = []
        
        # Tone
        guidelines.append(f"Tone: {TONE_DESCRIPTIONS.get(prefs.tone, TONE_DESCRIPTIONS['balanced'])}")
        
        # Response length
        if prefs.response_length == "concise":
            guidelines.append("Response Length: Keep responses short and focused. Use bullet points and numbered lists.")
        elif prefs.response_length == "detailed":
            guidelines.append("Response Length: Provide comprehensive, detailed responses with examples and explanations.")
        else:  # adaptive
            guidelines.append("Response Length: Adapt length to the question complexity. Simple questions get simple answers.")
        
        # Expertise
        guidelines.append(f"User Expertise: {EXPERTISE_DESCRIPTIONS.get(expertise, EXPERTISE_DESCRIPTIONS['intermediate'])}")
        
        # Humor
        humor_level = round(prefs.humor_level * 5) / 5  # Round to nearest 0.2
        for level, desc in sorted(HUMOR_DESCRIPTIONS.items()):
            if humor_level <= level:
                guidelines.append(f"Humor: {desc}")
                break
        
        # Topic-specific adjustments
        if topic == "coding":
            guidelines.append("For coding questions: Include code examples, explain logic, mention best practices.")
        elif topic == "writing":
            guidelines.append("For writing tasks: Focus on clarity, flow, and style. Provide alternatives when appropriate.")
        elif topic == "analysis":
            guidelines.append("For analysis: Be thorough, cite sources when possible, structure findings clearly.")
        
        return "\n".join(f"- {g}" for g in guidelines)

    def _format_memories_for_prompt(self, memories: list[UserMemory]) -> str:
        """Format user memories into a prompt section."""
        if not memories:
            return ""
        
        memory_lines = []
        for mem in memories[:10]:  # Limit to top 10 most relevant
            if mem.memory_type == "preference":
                memory_lines.append(f"User preference: {mem.key} = {mem.value}")
            elif mem.memory_type == "expertise":
                memory_lines.append(f"Known expertise: {mem.key} ({mem.confidence:.0%} confidence)")
            elif mem.memory_type == "style_pattern":
                memory_lines.append(f"Style pattern: {mem.key}")
        
        if memory_lines:
            return "Learned user context:\n" + "\n".join(f"- {line}" for line in memory_lines)
        return ""

    async def build_system_prompt(
        self,
        user_id: str,
        conversation_history: list[dict],
        base_prompt: str
    ) -> str:
        """Build a dynamic system prompt based on user preferences and context.
        
        Args:
            user_id: The user's ID
            conversation_history: Current conversation messages
            base_prompt: The base Boost AI identity prompt
            
        Returns:
            Enhanced system prompt with personality adaptations
        """
        # Load user data
        prefs = await self.get_user_preferences(user_id)
        memories = await self.get_user_memories(user_id)
        feedback_patterns = await self.get_feedback_patterns(user_id)
        
        # Detect context
        topic = self._detect_topic(conversation_history)
        expertise = self._estimate_expertise_from_context(conversation_history, memories)
        
        # Override expertise if user has set a specific level
        if prefs.expertise_level != "auto":
            expertise = prefs.expertise_level
        
        # Build prompt sections
        behavioral_guidelines = self._get_behavioral_guidelines(prefs, topic, expertise)
        memory_section = self._format_memories_for_prompt(memories)
        
        # Add feedback-derived insights
        feedback_insights = ""
        if feedback_patterns:
            top_patterns = feedback_patterns[:5]
            feedback_insights = "Learned from feedback:\n" + "\n".join(
                f"- {p.pattern}" for p in top_patterns if p.pattern
            )
        
        # Construct final prompt
        prompt_parts = [
            base_prompt,
            f"\n\nCurrent Conversation Context:",
            f"- Detected topic: {topic}",
            f"- User expertise level: {expertise}",
            f"- Response style: {prefs.response_length}",
            "",
            "Behavioral Guidelines:",
            behavioral_guidelines,
        ]
        
        if memory_section:
            prompt_parts.extend(["", memory_section])
        
        if feedback_insights:
            prompt_parts.extend(["", feedback_insights])
        
        return "\n".join(prompt_parts)


# Singleton factory
_personality_engine = None


def get_personality_engine(db: AsyncSession) -> PersonalityEngine:
    """Get or create a PersonalityEngine instance."""
    return PersonalityEngine(db)