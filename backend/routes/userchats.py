from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import UserChat
from schemas import UserChatEntry
from services.auth import get_current_user_id
from services.cache import cache
from services.rate_limit import limiter
from settings import settings

router = APIRouter(prefix="/api/userchats", tags=["userchats"])


@router.get("")
@limiter.limit(settings.RATE_LIMIT_READ)
async def get_user_chats(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    cached = await cache.get("userchats", user_id)
    if cached:
        return cached

    result = await db.execute(
        select(UserChat)
        .where(UserChat.user_id == user_id)
        .order_by(UserChat.created_at.desc())
    )
    entries = result.scalars().all()

    response = [
        UserChatEntry(
            id=entry.chat_id,
            title=entry.title,
            is_shared=entry.is_shared,
            created_at=entry.created_at,
        ).to_frontend()
        for entry in entries
    ]

    await cache.set("userchats", user_id, response)
    return response
