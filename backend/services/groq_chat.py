"""Chat streaming via the multi-provider LLM router.

This module is now a thin wrapper around ``services.llm_router``.
It preserves the original ``stream_chat_response`` async-generator
interface so that ``routes/chats.py`` needs minimal changes.
"""
import asyncio
import threading
from typing import AsyncIterator

# Semaphore limits concurrent LLM threads to prevent thread explosion.
_llm_semaphore = threading.Semaphore(10)

# Import the sync streaming function from the router.
from services.llm_router import stream_chat_response as _sync_stream  # noqa: E402


async def stream_chat_response(
    history: list[dict],
    raw_history: list[dict] | None = None,
    user_id: str | None = None,
    system_prompt: str | None = None,
) -> AsyncIterator[str]:
    """Yield text chunks from the best available LLM provider.

    Runs the synchronous provider call in a background thread with a
    semaphore to cap concurrency.

    Args:
        history: Text-only conversation history [{role, content}].
        raw_history: Full chat history from DB with possible ``img`` fields.
                     Used by the router to detect images and route to vision.
        user_id: Optional user ID for personalized prompts.
        system_prompt: Optional pre-built system prompt (from personality engine).
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _worker():
        try:
            with _llm_semaphore:
                for chunk in _sync_stream(history, raw_history, user_id, system_prompt):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, exc)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    while True:
        item = await queue.get()
        if item is None:
            break
        if isinstance(item, Exception):
            raise item
        yield item
