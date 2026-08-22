"""Title generation via the multi-provider LLM router.

The sync ``generate_title`` function from ``llm_router`` is called inside
``asyncio.to_thread`` so it no longer blocks the event loop.
"""
import asyncio
from services.llm_router import generate_title as _sync_generate_title  # noqa: E402


async def generate_chat_title(history: list[dict]) -> str:
    """Generate a short, concise title for a chat conversation.

    Runs the synchronous Groq/OpenRouter call in a thread pool so the
    asyncio event loop is never blocked.
    """
    try:
        return await asyncio.to_thread(_sync_generate_title, history)
    except Exception as e:
        print(f"Title generation failed: {e}")
        return ""
