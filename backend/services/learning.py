"""Learning Engine - Feedback analysis and pattern extraction.

This module processes user feedback (likes/dislikes) to learn:
- What response characteristics users prefer
- Tone and style preferences
- Topic-specific patterns
- Global feedback trends
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserPreference, UserMemory, FeedbackAnalytics, Chat

log = logging.getLogger("learning")

# Minimum feedback signals before applying learning (conservative approach)
MIN_FEEDBACK_THRESHOLD = 5

# Categories for feedback classification
FEEDBACK_CATEGORIES = {
    "response_quality": ["like", "dislike"],
    "tone_match": ["too_formal", "too_casual", "just_right"],
    "length_preference": ["too_long", "too_short", "just_right"],
    "accuracy": ["accurate", "inaccurate", "partially_accurate"],
    "helpfulness": ["helpful", "unhelpful", "partially_helpful"],
}


class FeedbackAnalyzer:
    """Analyzes user feedback to extract patterns and improve responses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_feedback(
        self,
        user_id: str,
        chat_id: str,
        message_index: int,
        feedback_type: str,
        response_text: str,
        user_message: str
    ) -> dict:
        """Process a single feedback event and update learning.
        
        Args:
            user_id: The user providing feedback
            chat_id: The chat containing the message
            message_index: Index of the message in the conversation
            feedback_type: 'like', 'dislike', or 'none'
            response_text: The AI response that received feedback
            user_message: The user message that triggered the response
            
        Returns:
            dict with learning updates applied
        """
        if feedback_type == "none":
            return {"action": "cleared", "learned": False}
        
        # Update user preference feedback count
        prefs_result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        prefs = prefs_result.scalar_one_or_none()
        
        if prefs:
            prefs.feedback_count += 1
            prefs.updated_at = datetime.now(timezone.utc)
        
        # Extract response characteristics
        characteristics = self._extract_characteristics(response_text, user_message)
        
        # Store feedback pattern
        await self._store_feedback_pattern(
            user_id=user_id,
            feedback_type=feedback_type,
            characteristics=characteristics
        )
        
        # Check if we should apply learning
        feedback_count = (prefs.feedback_count if prefs else 0)
        learned = False
        
        if feedback_count >= MIN_FEEDBACK_THRESHOLD:
            learned = await self._apply_learned_preferences(user_id, feedback_count)
        
        return {
            "action": feedback_type,
            "learned": learned,
            "feedback_count": feedback_count,
            "threshold": MIN_FEEDBACK_THRESHOLD,
            "characteristics": characteristics,
        }

    def _extract_characteristics(self, response_text: str, user_message: str) -> dict:
        """Extract characteristics from a response for pattern learning."""
        characteristics = {
            "length": self._classify_length(response_text),
            "has_code": "```" in response_text or "code" in response_text.lower(),
            "has_list": any(line.strip().startswith(("-", "*", "1.", "2.")) for line in response_text.split("\n")),
            "has_example": "example" in response_text.lower() or "for instance" in response_text.lower(),
            "tone_indicators": self._detect_tone_indicators(response_text),
            "question_complexity": self._classify_question_complexity(user_message),
        }
        return characteristics

    def _classify_length(self, text: str) -> str:
        """Classify response length."""
        word_count = len(text.split())
        if word_count < 50:
            return "short"
        elif word_count < 200:
            return "medium"
        else:
            return "long"

    def _detect_tone_indicators(self, text: str) -> list[str]:
        """Detect tone indicators in the response."""
        indicators = []
        text_lower = text.lower()
        
        # Formal indicators
        formal_words = ["furthermore", "consequently", "therefore", "moreover", "additionally"]
        if any(word in text_lower for word in formal_words):
            indicators.append("formal")
        
        # Casual indicators
        casual_words = ["hey", "sure", "yeah", "cool", "awesome", "gonna", "wanna"]
        if any(word in text_lower for word in casual_words):
            indicators.append("casual")
        
        # Enthusiastic indicators
        if "!" in text and text.count("!") > 2:
            indicators.append("enthusiastic")
        
        # Technical indicators
        technical_words = ["implementation", "architecture", "algorithm", "optimization", "throughput"]
        if any(word in text_lower for word in technical_words):
            indicators.append("technical")
        
        return indicators

    def _classify_question_complexity(self, question: str) -> str:
        """Classify the complexity of the user's question."""
        question_lower = question.lower()
        
        # Simple questions
        simple_patterns = ["what is", "how do", "can you", "define", "explain"]
        if any(pattern in question_lower for pattern in simple_patterns):
            return "simple"
        
        # Complex questions
        complex_patterns = ["implement", "optimize", "architect", "design pattern", "trade-off", "compare"]
        if any(pattern in question_lower for pattern in complex_patterns):
            return "complex"
        
        return "medium"

    async def _store_feedback_pattern(
        self,
        user_id: str,
        feedback_type: str,
        characteristics: dict
    ) -> None:
        """Store feedback pattern for later analysis."""
        # Create pattern description
        pattern_parts = []
        
        if characteristics["has_code"]:
            pattern_parts.append("code_examples")
        if characteristics["has_list"]:
            pattern_parts.append("structured_lists")
        if characteristics["has_example"]:
            pattern_parts.append("practical_examples")
        
        length_pattern = f"{characteristics['length']}_responses"
        pattern_parts.append(length_pattern)
        
        tone = characteristics.get("tone_indicators", [])
        if tone:
            pattern_parts.append(f"tone:{tone[0]}")
        
        pattern = " + ".join(pattern_parts) if pattern_parts else "general"
        category = "response_quality"
        
        # Check if this pattern already exists
        result = await self.db.execute(
            select(FeedbackAnalytics).where(
                FeedbackAnalytics.user_id == user_id,
                FeedbackAnalytics.category == category,
                FeedbackAnalytics.pattern == pattern
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            if feedback_type == "like":
                existing.positive_count += 1
            else:
                existing.negative_count += 1
            existing.last_updated = datetime.now(timezone.utc)
        else:
            new_analytics = FeedbackAnalytics(
                user_id=user_id,
                category=category,
                pattern=pattern,
                positive_count=1 if feedback_type == "like" else 0,
                negative_count=1 if feedback_type == "dislike" else 0,
            )
            self.db.add(new_analytics)
        
        await self.db.flush()

    async def _apply_learned_preferences(self, user_id: str, feedback_count: int) -> bool:
        """Apply learned preferences based on accumulated feedback.
        
        Returns True if preferences were updated.
        """
        # Get feedback patterns
        result = await self.db.execute(
            select(FeedbackAnalytics).where(
                FeedbackAnalytics.user_id == user_id,
                FeedbackAnalytics.category == "response_quality"
            ).order_by(FeedbackAnalytics.positive_count.desc())
        )
        patterns = list(result.scalars().all())
        
        if not patterns:
            return False
        
        # Find the most liked pattern
        top_pattern = patterns[0]
        
        # Only apply if there's a clear winner (positive significantly outweighs negative)
        if top_pattern.positive_count < 3:
            return False
        
        if top_pattern.negative_count > top_pattern.positive_count * 0.5:
            return False  # Too controversial, don't apply
        
        # Extract preference updates from pattern
        updates = {}
        
        if "short_responses" in top_pattern.pattern:
            updates["response_length"] = "concise"
        elif "long_responses" in top_pattern.pattern:
            updates["response_length"] = "detailed"
        elif "medium_responses" in top_pattern.pattern:
            updates["response_length"] = "adaptive"
        
        if "tone:formal" in top_pattern.pattern:
            updates["tone"] = "formal"
        elif "tone:casual" in top_pattern.pattern:
            updates["tone"] = "casual"
        elif "tone:technical" in top_pattern.pattern:
            updates["expertise_level"] = "expert"
        
        if updates:
            # Update user preferences
            prefs_result = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            prefs = prefs_result.scalar_one_or_none()
            
            if prefs:
                for key, value in updates.items():
                    if hasattr(prefs, key):
                        setattr(prefs, key, value)
                
                prefs.last_adapted_at = datetime.now(timezone.utc)
                prefs.updated_at = datetime.now(timezone.utc)
                await self.db.flush()
                
                log.info("Applied learned preferences for user %s: %s", user_id, updates)
                return True
        
        return False

    async def get_global_patterns(self, limit: int = 20) -> list[FeedbackAnalytics]:
        """Get global feedback patterns across all users."""
        result = await self.db.execute(
            select(FeedbackAnalytics)
            .where(FeedbackAnalytics.user_id.is_(None))
            .order_by(FeedbackAnalytics.positive_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user_learning_summary(self, user_id: str) -> dict:
        """Get a summary of what has been learned about a user."""
        # Get preference
        prefs_result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        prefs = prefs_result.scalar_one_or_none()
        
        # Get memories
        memories_result = await self.db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        memories = list(memories_result.scalars().all())
        
        # Get feedback patterns
        patterns_result = await self.db.execute(
            select(FeedbackAnalytics).where(FeedbackAnalytics.user_id == user_id)
        )
        patterns = list(patterns_result.scalars().all())
        
        return {
            "preferences": {
                "tone": prefs.tone if prefs else "balanced",
                "response_length": prefs.response_length if prefs else "adaptive",
                "expertise_level": prefs.expertise_level if prefs else "auto",
                "humor_level": prefs.humor_level if prefs else 0.5,
                "feedback_count": prefs.feedback_count if prefs else 0,
                "last_adapted": prefs.last_adapted_at.isoformat() if prefs and prefs.last_adapted_at else None,
            },
            "memories_count": len(memories),
            "patterns_count": len(patterns),
            "top_patterns": [
                {"pattern": p.pattern, "positive": p.positive_count, "negative": p.negative_count}
                for p in patterns[:5]
            ],
        }


def get_feedback_analyzer(db: AsyncSession) -> FeedbackAnalyzer:
    """Get or create a FeedbackAnalyzer instance."""
    return FeedbackAnalyzer(db)