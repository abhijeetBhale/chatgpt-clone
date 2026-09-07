import uuid
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Chat, UserChat
from schemas import (
    CreateChatRequest, UpdateChatRequest, MessageRequest,
    FeedbackRequest, ShareRequest, EditMessageRequest, ChatResponse
)
from services.auth import get_current_user_id
from services.groq_title import generate_chat_title
from services.groq_chat import stream_chat_response
from services.cache import cache
from services.rate_limit import limiter
from services.plans import ai_limit, read_limit, mutate_limit
from services import flags
from settings import settings

log = logging.getLogger("chats")

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("", status_code=201)
@limiter.limit(ai_limit)
async def create_chat(
    request: Request,
    body: CreateChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    chat_title = body.text[:40] if body.text else "New Chat"

    new_chat = Chat(
        user_id=user_id,
        history=[{"role": "user", "parts": [{"text": body.text}]}],
    )
    db.add(new_chat)
    await db.flush()

    user_chat_entry = UserChat(
        user_id=user_id,
        chat_id=new_chat.id,
        title=chat_title,
    )
    db.add(user_chat_entry)
    await db.flush()

    await cache.delete("userchats", user_id)

    return {"_id": str(new_chat.id)}


@router.get("/{chat_id}")
@limiter.limit(read_limit)
async def get_chat(
    request: Request,
    chat_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"{user_id}:{chat_id}"
    cached = await cache.get("chat", cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    response = ChatResponse(
        id=chat.id,
        user_id=chat.user_id,
        history=chat.history,
        is_shared=chat.is_shared,
        feedback=chat.feedback,
        edit_history=chat.edit_history or [],
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    ).to_frontend()

    await cache.set("chat", cache_key, response)
    return response


@router.get("/shared/{chat_id}")
@limiter.limit(read_limit)
async def get_shared_chat(
    request: Request,
    chat_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    cached = await cache.get("shared_chat", str(chat_id))
    if cached:
        return cached

    # Feature flag gate — sharing disabled hides all public chat links
    if not await flags.is_enabled(db, "enable_chat_sharing"):
        raise HTTPException(status_code=404, detail="Shared chat not found or not shared")

    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.is_shared == True)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Shared chat not found or not shared")

    response = ChatResponse(
        id=chat.id,
        user_id=chat.user_id,
        history=chat.history,
        is_shared=chat.is_shared,
        feedback={},
        edit_history=[],
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    ).to_frontend()

    await cache.set("shared_chat", str(chat_id), response, ttl=600)
    return response


@router.put("/{chat_id}")
@limiter.limit(mutate_limit)
async def update_chat(
    request: Request,
    chat_id: uuid.UUID,
    body: UpdateChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    new_items = []
    if body.question:
        user_msg = {"role": "user", "parts": [{"text": body.question}]}
        if body.img:
            user_msg["img"] = body.img
        new_items.append(user_msg)

    new_items.append({"role": "model", "parts": [{"text": body.answer}]})

    updated_history = chat.history + new_items

    await db.execute(
        update(Chat)
        .where(Chat.id == chat_id, Chat.user_id == user_id)
        .values(history=updated_history)
    )

    if len(updated_history) == 2:
        title = await generate_chat_title(updated_history)
        if title:
            await db.execute(
                update(UserChat)
                .where(UserChat.chat_id == chat_id, UserChat.user_id == user_id)
                .values(title=title)
            )

    await cache.delete("chat", f"{user_id}:{chat_id}")
    await cache.delete("userchats", user_id)

    return {"status": "ok"}


@router.post("/{chat_id}/message")
@limiter.limit(ai_limit)
async def send_message(
    request: Request,
    chat_id: uuid.UUID,
    body: MessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if body.question:
        user_msg = {"role": "user", "parts": [{"text": body.question}]}
        if body.img:
            user_msg["img"] = body.img
        updated_history = chat.history + [user_msg]
        await db.execute(
            update(Chat)
            .where(Chat.id == chat_id, Chat.user_id == user_id)
            .values(history=updated_history)
        )
        await db.commit()
        await db.refresh(chat)
    else:
        await db.refresh(chat)

    log.info("send_message: chat_id=%s, body.img=%s, chat.history_len=%d", chat_id, body.img, len(chat.history))
    for i, msg in enumerate(chat.history):
        log.debug("chat.history[%d]: role=%s, has_img=%s, img=%s", i, msg.get("role"), bool(msg.get("img")), msg.get("img"))

    conversation_history = [
        {"role": "assistant" if msg["role"] == "model" else "user", "content": msg["parts"][0].get("text", "")}
        for msg in chat.history
    ]

    # Build RAG-enhanced system prompt
    system_prompt = None
    try:
        from services.rag_context import get_rag_context_service
        rag_service = get_rag_context_service(db)
        
        # Get the user's latest message for context retrieval
        user_message = ""
        if body.question:
            user_message = body.question
        elif chat.history:
            last_user_msg = next(
                (m for m in reversed(chat.history) if m.get("role") == "user"), 
                None
            )
            if last_user_msg:
                user_message = last_user_msg.get("parts", [{}])[0].get("text", "")
        
        system_prompt = await rag_service.build_rag_enhanced_prompt(
            user_id=user_id,
            user_message=user_message,
            conversation_history=conversation_history,
            base_prompt="You are Boost AI, an advanced AI assistant platform built by Abhijeet Bhale.",
            current_chat_id=str(chat_id)
        )
    except Exception as exc:
        log.warning("Failed to build RAG prompt: %s — using default", exc)

    async def event_generator():
        accumulated = ""
        try:
            async for chunk in stream_chat_response(
                conversation_history, 
                chat.history,
                user_id=user_id,
                system_prompt=system_prompt
            ):
                accumulated += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            if accumulated:
                ai_msg = {"role": "model", "parts": [{"text": accumulated}]}
                new_history = chat.history + [ai_msg]
                await db.execute(
                    update(Chat)
                    .where(Chat.id == chat_id, Chat.user_id == user_id)
                    .values(history=new_history)
                )
                await db.commit()

                # Process conversation for RAG and auto-learning
                try:
                    from services.rag_context import get_rag_context_service
                    rag_service = get_rag_context_service(db)
                    last_user_msg = next(
                        (m for m in reversed(chat.history) if m.get("role") == "user"),
                        None
                    )
                    last_user_text = last_user_msg.get("parts", [{}])[0].get("text", "") if last_user_msg else ""
                    await rag_service.process_conversation_turn(
                        user_id=user_id,
                        chat_id=str(chat_id),
                        user_message=last_user_text,
                        ai_response=accumulated,
                        conversation_history=chat.history
                    )
                    await db.commit()
                except Exception as exc:
                    log.warning("Failed to process RAG/learning: %s", exc)

            await cache.delete("chat", f"{user_id}:{chat_id}")

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.put("/{chat_id}/feedback")
@limiter.limit(mutate_limit)
async def update_feedback(
    request: Request,
    chat_id: uuid.UUID,
    body: FeedbackRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    feedback = chat.feedback or {}
    message_key = str(body.message_index)

    if body.feedback_type == "none":
        feedback.pop(message_key, None)
    else:
        feedback[message_key] = body.feedback_type

    await db.execute(
        update(Chat)
        .where(Chat.id == chat_id, Chat.user_id == user_id)
        .values(feedback=feedback)
    )
    await db.commit()

    # Process feedback for learning
    learning_result = None
    try:
        from services.learning import get_feedback_analyzer
        analyzer = get_feedback_analyzer(db)
        
        # Extract user message and AI response for learning
        message_index = body.message_index
        if 0 <= message_index < len(chat.history):
            # Get the user message (previous message)
            user_message = ""
            if message_index > 0:
                prev_msg = chat.history[message_index - 1]
                user_message = prev_msg.get("parts", [{}])[0].get("text", "")
            
            # Get the AI response
            ai_response = chat.history[message_index].get("parts", [{}])[0].get("text", "")
            
            learning_result = await analyzer.process_feedback(
                user_id=user_id,
                chat_id=str(chat_id),
                message_index=message_index,
                feedback_type=body.feedback_type,
                response_text=ai_response,
                user_message=user_message
            )
    except Exception as exc:
        log.warning("Failed to process feedback for learning: %s", exc)

    await cache.delete("chat", f"{user_id}:{chat_id}")

    return {
        "status": "ok", 
        "feedback": feedback,
        "learning": learning_result
    }


@router.put("/{chat_id}/share")
@limiter.limit(mutate_limit)
async def update_share_status(
    request: Request,
    chat_id: uuid.UUID,
    body: ShareRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Feature flag gate — admins can turn sharing off globally from /admin
    if not await flags.is_enabled(db, "enable_chat_sharing"):
        raise HTTPException(status_code=403, detail="Chat sharing is currently disabled")

    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await db.execute(
        update(Chat)
        .where(Chat.id == chat_id, Chat.user_id == user_id)
        .values(is_shared=body.is_shared)
    )

    await db.execute(
        update(UserChat)
        .where(UserChat.chat_id == chat_id, UserChat.user_id == user_id)
        .values(is_shared=body.is_shared)
    )

    await db.commit()

    await cache.delete("chat", f"{user_id}:{chat_id}")
    await cache.delete("shared_chat", str(chat_id))
    await cache.delete("userchats", user_id)

    return {"status": "ok", "is_shared": body.is_shared}


@router.put("/{chat_id}/edit")
@limiter.limit(mutate_limit)
async def edit_message(
    request: Request,
    chat_id: uuid.UUID,
    body: EditMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    edit_history = chat.edit_history or []
    edit_entry = {
        "message_index": body.message_index,
        "original_text": body.original_text,
        "edited_text": body.edited_text,
        "edited_at": datetime.now(timezone.utc).isoformat(),
    }
    edit_history.append(edit_entry)

    history = chat.history
    if 0 <= body.message_index < len(history):
        history[body.message_index]["parts"][0]["text"] = body.edited_text

    await db.execute(
        update(Chat)
        .where(Chat.id == chat_id, Chat.user_id == user_id)
        .values(history=history, edit_history=edit_history)
    )
    await db.commit()

    await cache.delete("chat", f"{user_id}:{chat_id}")

    return {"status": "ok", "edit_history": edit_history}
