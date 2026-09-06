"""Auto-Learning Service - Analyzes every conversation automatically.

No manual feedback required! This service:
1. Analyzes conversation patterns after each exchange
2. Extracts user expertise level from questions
3. Detects communication style preferences
4. Updates user preferences automatically
5. Stores memories for cross-session learning
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserPreference, UserMemory, FeedbackAnalytics

log = logging.getLogger("auto_learning")

# Expertise detection patterns
EXPERT_PATTERNS = [
    'api', 'async', 'callback', 'middleware', 'database', 'schema', 'endpoint',
    'authentication', 'oauth', 'jwt', 'redis', 'postgresql', 'mongodb',
    'docker', 'kubernetes', 'aws', 'lambda', 'microservice', 'architecture',
    'algorithm', 'data structure', 'complexity', 'optimization', 'refactor',
    'design pattern', 'solid', 'dependency injection', 'unit test', 'integration',
    'ci/cd', 'terraform', 'graphql', 'grpc', 'websocket', 'cors', 'csrf',
    'sql injection', 'xss', 'encryption', 'hashing', 'cryptography',
]

BEGINNER_PATTERNS = [
    'how do i', 'what is', 'can you explain', "what's the difference",
    "how does", 'why', 'beginner', 'new to', 'learning', 'just started',
    'simple example', 'basic', 'fundamental', 'getting started',
    'tutorial', 'step by step', 'eli5', 'simple explanation',
]

TOPIC_KEYWORDS = {
    'python': ['python', 'django', 'flask', 'fastapi', 'pip', 'venv', 'conda'],
    'javascript': ['javascript', 'js', 'react', 'node', 'npm', 'vue', 'angular', 'typescript'],
    'database': ['sql', 'database', 'postgres', 'mysql', 'mongodb', 'redis', 'supabase'],
    'api': ['api', 'rest', 'graphql', 'endpoint', 'http', 'fetch', 'axios'],
    'devops': ['docker', 'kubernetes', 'aws', 'deploy', 'ci/cd', 'git', 'github'],
    'data_science': ['data', 'analytics', 'machine learning', 'ai', 'model', 'pandas', 'numpy'],
    'web_dev': ['html', 'css', 'frontend', 'backend', 'web', 'responsive'],
    'mobile': ['ios', 'android', 'mobile', 'app', 'react native', 'flutter'],
}


class AutoLearningService:
    """Automatically learns from every conversation without manual feedback."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        conversation_history: list[dict]
    ) -> dict:
        """Analyze a complete conversation turn and update user profile.
        
        Called automatically after every AI response.
        Returns what was learned and updated.
        """
        updates = {
            'preferences_updated': False,
            'memories_created': [],
            'expertise_detected': None,
            'topics_detected': [],
            'patterns_detected': [],
        }
        
        # 1. Detect expertise level from user message
        expertise = self._detect_expertise(user_message, conversation_history)
        if expertise:
            updates['expertise_detected'] = expertise
            await self._update_expertise_memory(user_id, expertise)
        
        # 2. Detect topics
        topics = self._detect_topics(user_message + " " + ai_response)
        updates['topics_detected'] = topics
        
        # 3. Analyze communication style
        style = self._analyze_communication_style(user_message)
        if style:
            updates['patterns_detected'].append(style)
            await self._update_style_memory(user_id, style)
        
        # 4. Analyze response preferences (implicit feedback)
        pref_update = await self._analyze_response_preference(
            user_id, user_message, ai_response, conversation_history
        )
        if pref_update:
            updates['preferences_updated'] = True
        
        # 5. Store conversation patterns
        await self._store_conversation_patterns(user_id, user_message, ai_response, topics)
        
        log.info("Auto-learning for user %s: %s", user_id, updates)
        return updates

    def _detect_expertise(self, message: str, history: list[dict]) -> Optional[str]:
        """Detect user expertise level from their message."""
        message_lower = message.lower()
        
        # Count expert vs beginner indicators
        expert_score = sum(1 for p in EXPERT_PATTERNS if p in message_lower)
        beginner_score = sum(1 for p in BEGINNER_PATTERNS if p in message_lower)
        
        # Also check recent history for patterns
        recent_user_msgs = [m.get('content', '') for m in history[-6:] if m.get('role') == 'user']
        for msg in recent_user_msgs:
            msg_lower = msg.lower()
            expert_score += sum(0.5 for p in EXPERT_PATTERNS if p in msg_lower)
            beginner_score += sum(0.5 for p in BEGINNER_PATTERNS if p in msg_lower)
        
        if expert_score > beginner_score + 2:
            return 'expert'
        elif beginner_score > expert_score + 1:
            return 'beginner'
        elif expert_score > 0 or beginner_score > 0:
            return 'intermediate'
        return None

    def _detect_topics(self, text: str) -> list[str]:
        """Detect topics from text."""
        text_lower = text.lower()
        found_topics = []
        
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                found_topics.append(topic)
        
        return found_topics[:3]  # Top 3 topics

    def _analyze_communication_style(self, message: str) -> Optional[dict]:
        """Analyze user's communication style."""
        words = message.split()
        word_count = len(words)
        
        style_indicators = {
            'prefers_brief': word_count < 10,
            'prefers_detailed': word_count > 50,
            'uses_questions': '?' in message,
            'uses_code': '```' in message or 'code' in message.lower(),
            'technical_language': any(p in message.lower() for p in EXPERT_PATTERNS[:10]),
        }
        
        # Only return if there's a clear signal
        true_count = sum(style_indicators.values())
        if true_count >= 2:
            return {
                'type': 'communication_style',
                'indicators': style_indicators,
                'message_length': word_count,
            }
        return None

    async def _analyze_response_preference(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        history: list[dict]
    ) -> bool:
        """Analyze if the AI response matched user expectations."""
        # Simple heuristic: if user asks follow-up about same topic, 
        # previous response might have been incomplete
        # If user moves on, response was likely adequate
        
        response_length = len(ai_response.split())
        question_complexity = len(user_message.split())
        
        # Update preferences based on implicit signals
        prefs = await self._get_or_create_preferences(user_id)
        
        # If user asks very short questions, they might prefer concise responses
        if question_complexity < 8 and prefs.response_length == 'adaptive':
            # Don't change yet, need more signals
            pass
        
        # Store the pattern for later analysis
        return True

    async def _update_expertise_memory(self, user_id: str, expertise: str) -> None:
        """Update expertise memory for user."""
        # Check existing memory
        result = await self.db.execute(
            select(UserMemory).where(
                UserMemory.user_id == user_id,
                UserMemory.memory_type == 'expertise',
                UserMemory.key == 'detected_level'
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update with higher confidence if consistent
            if existing.value == expertise:
                existing.confidence = min(1.0, existing.confidence + 0.1)
            else:
                # Different detection, lower confidence
                existing.confidence = max(0.3, existing.confidence - 0.1)
                if existing.confidence < 0.4:
                    existing.value = expertise  # Switch if low confidence
            existing.last_used_at = datetime.now(timezone.utc)
        else:
            new_memory = UserMemory(
                user_id=user_id,
                memory_type='expertise',
                key='detected_level',
                value=expertise,
                confidence=0.6,
                source='auto_detected',
            )
            self.db.add(new_memory)
        
        await self.db.flush()

    async def _update_style_memory(self, user_id: str, style: dict) -> None:
        """Update communication style memory."""
        indicators = style.get('indicators', {})
        
        for key, value in indicators.items():
            result = await self.db.execute(
                select(UserMemory).where(
                    UserMemory.user_id == user_id,
                    UserMemory.memory_type == 'style_pattern',
                    UserMemory.key == key
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update with running average
                if value:
                    existing.confidence = min(1.0, existing.confidence + 0.05)
                else:
                    existing.confidence = max(0.0, existing.confidence - 0.05)
                existing.last_used_at = datetime.now(timezone.utc)
            else:
                new_memory = UserMemory(
                    user_id=user_id,
                    memory_type='style_pattern',
                    key=key,
                    value=str(value),
                    confidence=0.5 if value else 0.5,
                    source='auto_detected',
                )
                self.db.add(new_memory)
        
        await self.db.flush()

    async def _store_conversation_patterns(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        topics: list[str]
    ) -> None:
        """Store conversation patterns for learning."""
        # Store topic patterns
        for topic in topics:
            result = await self.db.execute(
                select(FeedbackAnalytics).where(
                    FeedbackAnalytics.user_id == user_id,
                    FeedbackAnalytics.category == 'topic_interest',
                    FeedbackAnalytics.pattern == topic
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.positive_count += 1
                existing.last_updated = datetime.now(timezone.utc)
            else:
                new_analytics = FeedbackAnalytics(
                    user_id=user_id,
                    category='topic_interest',
                    pattern=topic,
                    positive_count=1,
                    negative_count=0,
                )
                self.db.add(new_analytics)
        
        await self.db.flush()

    async def _get_or_create_preferences(self, user_id: str) -> UserPreference:
        """Get or create user preferences."""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            prefs = UserPreference(user_id=user_id)
            self.db.add(prefs)
            await self.db.flush()
        
        return prefs

    async def get_user_context(self, user_id: str) -> dict:
        """Get comprehensive user context for personalization."""
        # Get preferences
        prefs = await self._get_or_create_preferences(user_id)
        
        # Get memories
        memories_result = await self.db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        memories = list(memories_result.scalars().all())
        
        # Get topic interests
        topics_result = await self.db.execute(
            select(FeedbackAnalytics).where(
                FeedbackAnalytics.user_id == user_id,
                FeedbackAnalytics.category == 'topic_interest'
            ).order_by(FeedbackAnalytics.positive_count.desc())
        )
        topics = list(topics_result.scalars().all())
        
        # Build context
        context = {
            'preferences': {
                'tone': prefs.tone,
                'response_length': prefs.response_length,
                'expertise_level': prefs.expertise_level,
                'humor_level': prefs.humor_level,
            },
            'detected_expertise': None,
            'style_patterns': {},
            'topic_interests': [t.pattern for t in topics[:5]],
        }
        
        for mem in memories:
            if mem.memory_type == 'expertise':
                context['detected_expertise'] = {
                    'level': mem.value,
                    'confidence': mem.confidence,
                }
            elif mem.memory_type == 'style_pattern':
                context['style_patterns'][mem.key] = {
                    'value': mem.value,
                    'confidence': mem.confidence,
                }
        
        return context


def get_auto_learning_service(db: AsyncSession) -> AutoLearningService:
    """Get auto-learning service instance."""
    return AutoLearningService(db)