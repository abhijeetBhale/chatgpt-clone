"""User Memory API endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth import get_current_user_id
from services.memory import get_memory_manager
from services.rate_limit import limiter
from services.plans import read_limit, mutate_limit

log = logging.getLogger("memory_routes")

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("")
@limiter.limit(read_limit)
async def get_memories(
    request: Request,
    memory_type: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all memories for the current user.
    
    Args:
        memory_type: Optional filter by type (expertise, preference, style_pattern, topic_expertise)
    """
    manager = get_memory_manager(db)
    memories = await manager.get_user_memories(user_id, memory_type=memory_type)
    
    return {
        "memories": [
            {
                "id": m.id,
                "memoryType": m.memory_type,
                "key": m.key,
                "value": m.value,
                "confidence": m.confidence,
                "source": m.source,
                "createdAt": m.created_at.isoformat(),
                "lastUsedAt": m.last_used_at.isoformat(),
                "expiresAt": m.expires_at.isoformat() if m.expires_at else None,
            }
            for m in memories
        ],
        "total": len(memories),
    }


@router.delete("/{memory_id}")
@limiter.limit(mutate_limit)
async def delete_memory(
    request: Request,
    memory_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific memory."""
    manager = get_memory_manager(db)
    deleted = await manager.delete_memory(user_id, memory_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"status": "ok", "deleted": True}


@router.delete("")
@limiter.limit(mutate_limit)
async def delete_all_memories(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete all memories for the current user."""
    manager = get_memory_manager(db)
    deleted_count = await manager.delete_all_memories(user_id)
    
    return {"status": "ok", "deleted_count": deleted_count}


@router.get("/export")
@limiter.limit(read_limit)
async def export_user_data(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export all user data (GDPR compliance)."""
    manager = get_memory_manager(db)
    data = await manager.export_user_data(user_id)
    return data