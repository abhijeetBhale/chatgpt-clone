"""Multi-provider LLM router with automatic failover.

Priority order:
  1. Groq   – fastest inference (~320 tok/s), free 30 RPM / 1K RPD
  2. Cerebras – 1M tokens/day free, ~1 800 tok/s
  3. OpenRouter – 20+ free models (DeepSeek V4-Flash, Qwen3.8 27B, etc.)

Each provider is tried in order.  On a 429 (rate-limit) or connection
error the router falls through to the next provider automatically.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Iterator, Optional

import httpx
from groq import Groq

from settings import settings

log = logging.getLogger("llm_router")

# ---------------------------------------------------------------------------
# Provider clients (lazy-initialised)
# ---------------------------------------------------------------------------

_groq: Optional[Groq] = None
_groq_lock = threading.Lock()

_cerebras_http: Optional[httpx.Client] = None
_cerebras_lock = threading.Lock()

_openrouter_http: Optional[httpx.Client] = None
_openrouter_lock = threading.Lock()


def _get_groq() -> Groq:
    global _groq
    if _groq is None:
        with _groq_lock:
            if _groq is None:
                _groq = Groq(api_key=settings.GROQ_API_KEY)
    return _groq


def _get_cerebras() -> httpx.Client:
    global _cerebras_http
    if _cerebras_http is None:
        with _cerebras_lock:
            if _cerebras_http is None:
                _cerebras_http = httpx.Client(
                    base_url="https://api.cerebras.ai/v1",
                    headers={"Authorization": f"Bearer {settings.CEREBRAS_API_KEY}"},
                    timeout=60.0,
                )
    return _cerebras_http


def _get_openrouter() -> httpx.Client:
    global _openrouter_http
    if _openrouter_http is None:
        with _openrouter_lock:
            if _openrouter_http is None:
                _openrouter_http = httpx.Client(
                    base_url="https://openrouter.ai/api/v1",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://boost-ai-chat.vercel.app",
                        "X-Title": "Boost AI",
                    },
                    timeout=60.0,
                )
    return _openrouter_http


# ---------------------------------------------------------------------------
# Provider definitions
# ---------------------------------------------------------------------------

@dataclass
class Provider:
    name: str
    model: str
    enabled: bool = True
    rpm_used: int = 0
    rpm_limit: int = 30
    _lock: field(default_factory=threading.Lock) = field(default_factory=threading.Lock, repr=False)


PROVIDERS = [
    # DeepSeek V4-Flash: best quality (88.1% GPQA), 1M context, free on OpenRouter
    Provider(name="openrouter", model="deepseek/deepseek-v4-flash:free", rpm_limit=20),
    # Groq GPT-OSS-120B: fastest inference (320+ tok/s), 128K context
    Provider(name="groq", model="openai/gpt-oss-120b", rpm_limit=30),
    # Cerebras: same model but free tier limited to 8K context
    Provider(name="cerebras", model="gpt-oss-120b", rpm_limit=5),
]

# Vision-capable provider (used when images are present in the conversation)
VISION_PROVIDER = Provider(name="cerebras_vision", model="gemma-4-31b", rpm_limit=5)

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


# ---------------------------------------------------------------------------
# Streaming implementations per provider
# ---------------------------------------------------------------------------

def _stream_groq(messages: list[dict]) -> Iterator[str]:
    """Stream chunks from Groq."""
    client = _get_groq()
    stream = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-120b",
        stream=True,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content or ""
        if content:
            yield content


def _stream_openrouter(messages: list[dict]) -> Iterator[str]:
    """Stream chunks from OpenRouter (SSE)."""
    client = _get_openrouter()
    with client.stream(
        "POST",
        "/chat/completions",
        json={
            "model": "deepseek/deepseek-v4-flash:free",
            "messages": messages,
            "stream": True,
        },
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload.strip() == "[DONE]":
                break
            import json
            try:
                obj = json.loads(payload)
                delta = obj.get("choices", [{}])[0].get("delta", {})
                text = delta.get("content", "")
                if text:
                    yield text
            except Exception:
                continue


def _stream_cerebras(messages: list[dict]) -> Iterator[str]:
    """Stream chunks from Cerebras (SSE, OpenAI-compatible)."""
    client = _get_cerebras()
    with client.stream(
        "POST",
        "/chat/completions",
        json={
            "model": "gpt-oss-120b",
            "messages": messages,
            "stream": True,
        },
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload.strip() == "[DONE]":
                break
            import json
            try:
                obj = json.loads(payload)
                delta = obj.get("choices", [{}])[0].get("delta", {})
                text = delta.get("content", "")
                if text:
                    yield text
            except Exception:
                continue


def _stream_openrouter_model(messages: list[dict], model: str) -> Iterator[str]:
    """Stream chunks from a specific OpenRouter model (SSE)."""
    client = _get_openrouter()
    with client.stream(
        "POST",
        "/chat/completions",
        json={
            "model": model,
            "messages": messages,
            "stream": True,
        },
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload.strip() == "[DONE]":
                break
            import json
            try:
                obj = json.loads(payload)
                delta = obj.get("choices", [{}])[0].get("delta", {})
                text = delta.get("content", "")
                if text:
                    yield text
            except Exception:
                continue


# Free vision-capable models on OpenRouter (tried in order)
VISION_PROVIDERS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
]


def _stream_cerebras_vision(messages: list[dict]) -> Iterator[str]:
    """Stream chunks from the best available free vision model.

    Tries OpenRouter vision models first (free), then Cerebras as fallback.
    Only yields once a provider succeeds completely.
    """
    errors = []

    # Try free OpenRouter vision models
    if settings.OPENROUTER_API_KEY:
        for model in VISION_PROVIDERS:
            try:
                chunks = list(_stream_openrouter_model(messages, model))
                log.info("Vision served by OpenRouter model: %s", model)
                for chunk in chunks:
                    yield chunk
                return
            except Exception as exc:
                errors.append(f"{model}: {exc}")
                log.warning("Vision model %s failed: %s — trying next", model, exc)

    # Fallback: Cerebras vision
    if settings.CEREBRAS_API_KEY:
        try:
            client = _get_cerebras()
            with client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": "gemma-4-31b",
                    "messages": messages,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                chunks = []
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    import json
                    try:
                        obj = json.loads(payload)
                        delta = obj.get("choices", [{}])[0].get("delta", {})
                        text = delta.get("content", "")
                        if text:
                            chunks.append(text)
                    except Exception:
                        continue
                for chunk in chunks:
                    yield chunk
                return
        except Exception as exc:
            errors.append(f"cerebras/gemma-4-31b: {exc}")
            log.warning("Cerebras vision failed: %s", exc)

    raise RuntimeError(f"All vision providers failed: {errors}")


def _has_images(history: list[dict]) -> bool:
    """Check if any message in the history contains an image."""
    for msg in history:
        if msg.get("img"):
            log.debug("Found image in message: img=%s, role=%s", msg.get("img"), msg.get("role"))
            return True
    return False


def _fetch_image_as_base64(imagekit_url: str) -> str:
    """Download image from ImageKit and return as base64 data URI."""
    import base64
    try:
        log.info("Fetching image from ImageKit: %s", imagekit_url)
        resp = httpx.get(imagekit_url, timeout=15.0)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/png")
        b64 = base64.b64encode(resp.content).decode("utf-8")
        data_uri = f"data:{content_type};base64,{b64}"
        log.info("Successfully fetched image, size: %d bytes, data_uri length: %d", len(resp.content), len(data_uri))
        return data_uri
    except Exception as exc:
        log.error("Failed to fetch image %s: %s", imagekit_url, exc, exc_info=True)
        return ""


def _build_vision_messages(history: list[dict]) -> list[dict]:
    """Build messages array with image content for vision models.

    Converts messages with 'img' field into OpenAI-compatible multimodal
    content format with base64-encoded images (required by Cerebras).
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history:
        role = "assistant" if msg.get("role") == "model" else "user"
        text = msg.get("parts", [{}])[0].get("text", "")
        img_path = msg.get("img")

        if img_path and role == "user":
            # Build full ImageKit URL and fetch as base64
            imagekit_url = f"{settings.IMAGEKIT_URL_ENDPOINT}{img_path}"
            log.info("Building vision message for image: %s", imagekit_url)
            data_uri = _fetch_image_as_base64(imagekit_url)
            if data_uri:
                content = [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ]
                messages.append({"role": role, "content": content})
                log.info("Added image to vision message, total messages: %d", len(messages))
            else:
                # Fallback: send text only if image fetch fails
                log.warning("Image fetch failed, sending text-only for this message")
                messages.append({"role": role, "content": text})
        else:
            messages.append({"role": role, "content": text})

    return messages


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stream_chat_response(
    history: list[dict],
    raw_history: list[dict] | None = None,
) -> Iterator[str]:
    """Yield text chunks from the best available LLM provider.

    If images are present in the raw_history, routes to Cerebras Gemma 4 31B
    (vision-capable) first. Otherwise tries providers in priority order.
    On 429 / connection errors falls through to the next one automatically.

    Args:
        history: Text-only conversation history [{role, content}].
        raw_history: Full chat history from DB with ``img`` fields.
                     Used to detect images and build vision messages.
    """
    # Use raw_history for image detection (it has the img fields)
    source = raw_history if raw_history is not None else history
    has_images = _has_images(source)
    
    log.info("stream_chat_response called: history_len=%d, raw_history_len=%d, has_images=%s, CEREBRAS_API_KEY=%s", 
             len(history), len(raw_history) if raw_history else 0, has_images, bool(settings.CEREBRAS_API_KEY))
    if raw_history:
        for i, msg in enumerate(raw_history):
            log.debug("raw_history[%d]: role=%s, has_img=%s, img=%s", 
                     i, msg.get("role"), bool(msg.get("img")), msg.get("img"))

    # If images present, try vision model first
    if has_images and (settings.OPENROUTER_API_KEY or settings.CEREBRAS_API_KEY):
        try:
            messages = _build_vision_messages(source)
            log.info("Routing to Cerebras Gemma 4 (vision) — images detected, %d messages", len(messages))
            chunks = list(_stream_cerebras_vision(messages))
            for chunk in chunks:
                yield chunk
            return
        except Exception as exc:
            log.warning("Vision provider failed: %s — falling back to text models", exc, exc_info=True)

    # Standard text-only routing
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    last_error: Optional[Exception] = None

    for provider in PROVIDERS:
        if not provider.enabled:
            continue

        try:
            if provider.name == "groq":
                chunks = list(_stream_groq(messages))
            elif provider.name == "cerebras":
                if not settings.CEREBRAS_API_KEY:
                    continue
                chunks = list(_stream_cerebras(messages))
            elif provider.name == "openrouter":
                if not settings.OPENROUTER_API_KEY:
                    continue
                chunks = list(_stream_openrouter(messages))
            else:
                continue

            log.info("LLM response served by %s", provider.name)
            for chunk in chunks:
                yield chunk
            return  # success — stop trying providers

        except Exception as exc:
            last_error = exc
            log.warning(
                "Provider %s failed: %s — trying next",
                provider.name,
                exc,
            )
            continue

    # All providers exhausted
    raise RuntimeError(
        f"All LLM providers failed. Last error: {last_error}"
    )


def generate_title(history: list[dict]) -> str:
    """Generate a short chat title (synchronous, called from a thread).

    Tries Groq first, falls back to OpenRouter.
    """
    small_model_messages = [
        {
            "role": "system",
            "content": (
                "Generate a short, concise title (max 40 characters) for this "
                "chat conversation. Only return the title, no quotes or extra text."
            ),
        },
    ]
    for msg in history:
        role = "assistant" if msg.get("role") == "model" else "user"
        text = ""
        if msg.get("parts") and len(msg["parts"]) > 0:
            text = msg["parts"][0].get("text", "")[:200]
        small_model_messages.append({"role": role, "content": text})

    # Try Groq (fast, small model)
    try:
        client = _get_groq()
        completion = client.chat.completions.create(
            messages=small_model_messages,
            model="llama-3.1-8b-instant",
            max_tokens=50,
            temperature=0.3,
        )
        title = completion.choices[0].message.content.strip().strip("\"'")[:40]
        log.info("Title generated via Groq: %s", title)
        return title
    except Exception as exc:
        log.warning("Groq title generation failed: %s", exc)

    # Fallback: OpenRouter (free small model)
    if settings.OPENROUTER_API_KEY:
        try:
            client = _get_openrouter()
            resp = client.post(
                "/chat/completions",
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct:free",
                    "messages": small_model_messages,
                    "max_tokens": 50,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            title = resp.json()["choices"][0]["message"]["content"].strip().strip("\"'")[:40]
            log.info("Title generated via OpenRouter: %s", title)
            return title
        except Exception as exc:
            log.warning("OpenRouter title generation failed: %s", exc)

    return ""
