from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import UserChat
from schemas import UserChatEntry
from services.auth import get_current_user_id

router = APIRouter(prefix="/api/userchats", tags=["userchats"])


@router.get("")
async def get_user_chats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all chats for the authenticated user, sorted by newest first."""
    result = await db.execute(
        select(UserChat)
        .where(UserChat.user_id == user_id)
        .order_by(UserChat.created_at.desc())
    )
    entries = result.scalars().all()

    return [
        UserChatEntry(
            id=entry.chat_id,
            title=entry.title,
            is_shared=entry.is_shared,
            created_at=entry.created_at,
        ).to_frontend()
        for entry in entries
    ]
