"""RAG Context Service - Retrieval-Augmented Generation for personalized responses.

Combines:
1. Vector search for relevant past conversations
2. Auto-learning insights
3. Conversation summaries
4. User preferences

All integrated into the prompt building process.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.embeddings import EmbeddingService, SummaryService, get_embedding_service, get_summary_service
from services.auto_learning import AutoLearningService, get_auto_learning_service
from services.personality import PersonalityEngine, get_personality_engine

log = logging.getLogger("rag_context")


class RAGContextService:
    """Retrieval-Augmented Generation context service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = get_embedding_service(db)
        self.summary_service = get_summary_service(db)
        self.auto_learning = get_auto_learning_service(db)
        self.personality_engine = get_personality_engine(db)

    async def build_rag_enhanced_prompt(
        self,
        user_id: str,
        user_message: str,
        conversation_history: list[dict],
        base_prompt: str,
        current_chat_id: str = None
    ) -> str:
        """Build a RAG-enhanced system prompt.
        
        This combines:
        1. User preferences (tone, expertise, etc.)
        2. Relevant past conversation context (via vector search)
        3. Auto-detected patterns
        4. Topic-specific instructions
        """
        # 1. Get user context from auto-learning
        user_context = await self.auto_learning.get_user_context(user_id)
        
        # 2. Search for relevant past conversations
        relevant_context = await self._retrieve_relevant_context(
            user_id, user_message, current_chat_id
        )
        
        # 3. Build enhanced prompt
        prompt_parts = [base_prompt]
        
        # Add user profile
        prefs = user_context.get('preferences', {})
        prompt_parts.append("\n\nUser Profile:")
        prompt_parts.append(f"- Preferred tone: {prefs.get('tone', 'balanced')}")
        prompt_parts.append(f"- Response style: {prefs.get('response_length', 'adaptive')}")
        
        detected_expertise = user_context.get('detected_expertise')
        if detected_expertise:
            confidence = detected_expertise.get('confidence', 0)
            if confidence > 0.6:
                prompt_parts.append(f"- Detected expertise: {detected_expertise['level']} ({confidence:.0%} confidence)")
        
        # Add style patterns
        style_patterns = user_context.get('style_patterns', {})
        if style_patterns:
            prompt_parts.append("\nCommunication patterns:")
            for key, pattern in style_patterns.items():
                if pattern['confidence'] > 0.5:
                    clean_key = key.replace('_', ' ').replace('prefers ', 'prefers ')
                    prompt_parts.append(f"- {clean_key}: {pattern['value']}")
        
        # Add topic interests
        topic_interests = user_context.get('topic_interests', [])
        if topic_interests:
            prompt_parts.append(f"\nUser's frequent topics: {', '.join(topic_interests)}")
        
        # Add relevant past context
        if relevant_context:
            prompt_parts.append("\n\nRelevant context from previous conversations:")
            for ctx in relevant_context[:3]:  # Top 3 most relevant
                prompt_parts.append(f"- {ctx['text'][:200]}...")
        
        # Add behavioral guidelines based on context
        prompt_parts.append("\n\nBehavioral Guidelines:")
        prompt_parts.append("- Adapt your response style to match the user's preferences")
        prompt_parts.append("- Use the detected expertise level to adjust explanation depth")
        prompt_parts.append("- Reference relevant past discussions when appropriate")
        prompt_parts.append("- Be helpful and maintain continuity across conversations")
        
        return "\n".join(prompt_parts)

    async def _retrieve_relevant_context(
        self,
        user_id: str,
        query_text: str,
        exclude_chat_id: str = None
    ) -> list[dict]:
        """Retrieve relevant context from past conversations."""
        try:
            # Search for similar conversation chunks
            similar_chunks = await self.embedding_service.search_similar(
                user_id=user_id,
                query_text=query_text,
                limit=5,
                exclude_chat_id=exclude_chat_id,
                chunk_types=['user_message', 'ai_response']
            )
            
            # Deduplicate and format
            seen_texts = set()
            relevant = []
            
            for chunk in similar_chunks:
                text = chunk['text']
                # Skip very similar texts
                text_hash = hash(text[:100])
                if text_hash not in seen_texts:
                    seen_texts.add(text_hash)
                    relevant.append({
                        'text': text,
                        'type': chunk['type'],
                        'similarity': chunk['similarity'],
                        'chat_id': chunk['chat_id'],
                    })
            
            return relevant
            
        except Exception as exc:
            log.warning("Failed to retrieve relevant context: %s", exc)
            return []

    async def process_conversation_turn(
        self,
        user_id: str,
        chat_id: str,
        user_message: str,
        ai_response: str,
        conversation_history: list[dict]
    ) -> dict:
        """Process a complete conversation turn for learning and storage.
        
        Called after every AI response to:
        1. Store embeddings for future retrieval
        2. Update auto-learning insights
        3. Update conversation summary
        """
        results = {
            'embedding_stored': False,
            'learning_updates': {},
            'summary_updated': False,
        }
        
        try:
            # 1. Store embeddings
            await self.embedding_service.store_conversation_turn(
                user_id=user_id,
                chat_id=chat_id,
                user_message=user_message,
                ai_response=ai_response
            )
            results['embedding_stored'] = True
            
        except Exception as exc:
            log.warning("Failed to store embeddings: %s", exc)
        
        try:
            # 2. Run auto-learning
            learning_updates = await self.auto_learning.analyze_conversation_turn(
                user_id=user_id,
                user_message=user_message,
                ai_response=ai_response,
                conversation_history=conversation_history
            )
            results['learning_updates'] = learning_updates
            
        except Exception as exc:
            log.warning("Failed to run auto-learning: %s", exc)
        
        try:
            # 3. Update summary
            await self.summary_service.update_summary(
                user_id=user_id,
                chat_id=chat_id,
                messages=conversation_history
            )
            results['summary_updated'] = True
            
        except Exception as exc:
            log.warning("Failed to update summary: %s", exc)
        
        return results


def get_rag_context_service(db: AsyncSession) -> RAGContextService:
    """Get RAG context service instance."""
    return RAGContextService(db)