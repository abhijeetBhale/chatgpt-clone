import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Chat, UserChat
from schemas import CreateChatRequest, UpdateChatRequest, ChatResponse
from services.auth import get_current_user_id
from services.groq_title import generate_chat_title

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("", status_code=201)
async def create_chat(
    body: CreateChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat with the user's first message."""
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

    return {"_id": str(new_chat.id)}


@router.get("/{chat_id}")
async def get_chat(
    chat_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single chat by ID."""
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatResponse(
        id=chat.id,
        user_id=chat.user_id,
        history=chat.history,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    ).to_frontend()


@router.put("/{chat_id}")
async def update_chat(
    chat_id: uuid.UUID,
    body: UpdateChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add messages to a chat and auto-generate title after first exchange."""
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

    return {"status": "ok"}
