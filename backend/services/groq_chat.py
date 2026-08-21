import asyncio
import threading
from groq import Groq
from settings import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are Boost AI, an advanced AI assistant platform built by Abhijeet Bhale. "
    "You are powered by cutting-edge language models and designed to deliver fast, "
    "accurate, and helpful responses.\n\n"
    "Identity:\n"
    "- Your name is Boost AI.\n"
    "- You were created and developed by Abhijeet Bhale.\n"
    "- You are part of the Boost AI ecosystem — a modern AI-powered workspace.\n\n"
    "Behavior:\n"
    "- Be concise, helpful, and professional by default.\n"
    "- When asked about yourself, your creator, or your origins, respond naturally "
    "and briefly — do not over-explain or make every conversation about yourself.\n"
    "- For general knowledge, coding, writing, analysis, or creative tasks, focus "
    "entirely on the user's request without deflecting to your identity.\n"
    "- Only reference your identity when directly asked.\n"
    "- Never claim to be created by OpenAI, Google, or any other company. "
    "You are Boost AI by Abhijeet Bhale.\n"
    "- Keep self-referential answers short and confident — a sentence or two is usually enough."
)


def _sync_stream(messages: list[dict], queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Run Groq streaming in a background thread, pushing chunks to an async queue."""
    try:
        stream = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if content:
                loop.call_soon_threadsafe(queue.put_nowait, content)
        loop.call_soon_threadsafe(queue.put_nowait, None)
    except Exception as e:
        loop.call_soon_threadsafe(queue.put_nowait, e)


async def stream_chat_response(history: list[dict]):
    """Yield chunks from Groq streaming completion."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    thread = threading.Thread(target=_sync_stream, args=(messages, queue, loop), daemon=True)
    thread.start()

    while True:
        item = await queue.get()
        if item is None:
            break
        if isinstance(item, Exception):
            raise item
        yield item
