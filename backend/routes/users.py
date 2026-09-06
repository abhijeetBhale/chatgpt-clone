"""User Management API endpoints - Admin visibility into platform users."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Chat, UserChat
from services.auth import get_current_user_id
from services.admin import is_admin_user
from services.rate_limit import limiter
from services.plans import read_limit

log = logging.getLogger("users")

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
@limiter.limit(read_limit)
async def list_users(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all users in the platform (admin only).
    
    Returns user IDs with chat counts and activity info.
    Since users are managed by Clerk, this queries the chats table
    to show which users have been active on the platform.
    """
    if not await is_admin_user(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get user statistics from chats table
    query = text("""
        SELECT 
            user_id,
            COUNT(DISTINCT c.id) as chat_count,
            COUNT(m.message_index) as message_count,
            MIN(c.created_at) as first_seen,
            MAX(c.updated_at) as last_active
        FROM chats c
        LEFT JOIN (
            SELECT 
                id as chat_id,
                jsonb_array_length(history) as message_index
            FROM chats
        ) m ON c.id = m.chat_id
        GROUP BY user_id
        ORDER BY last_active DESC
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    users = []
    for row in rows:
        users.append({
            "userId": row[0],
            "chatCount": row[1],
            "messageCount": row[2] if row[2] else 0,
            "firstSeen": row[3].isoformat() if row[3] else None,
            "lastActive": row[4].isoformat() if row[4] else None,
        })
    
    return {
        "users": users,
        "total": len(users),
    }


@router.get("/stats")
@limiter.limit(read_limit)
async def get_platform_stats(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get platform-wide statistics (admin only)."""
    if not await is_admin_user(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Total users
    users_result = await db.execute(
        select(func.count(func.distinct(Chat.user_id)))
    )
    total_users = users_result.scalar() or 0
    
    # Total chats
    chats_result = await db.execute(
        select(func.count(Chat.id))
    )
    total_chats = chats_result.scalar() or 0
    
    # Total messages (sum of history array lengths)
    messages_query = text("""
        SELECT SUM(jsonb_array_length(history)) FROM chats
    """)
    messages_result = await db.execute(messages_query)
    total_messages = messages_result.scalar() or 0
    
    # Active users (last 7 days)
    active_query = text("""
        SELECT COUNT(DISTINCT user_id) 
        FROM chats 
        WHERE updated_at > NOW() - INTERVAL '7 days'
    """)
    active_result = await db.execute(active_query)
    active_users_7d = active_result.scalar() or 0
    
    return {
        "totalUsers": total_users,
        "totalChats": total_chats,
        "totalMessages": total_messages,
        "activeUsersLast7Days": active_users_7d,
    }


@router.get("/{target_user_id}")
@limiter.limit(read_limit)
async def get_user_details(
    request: Request,
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info about a specific user (admin only)."""
    if not await is_admin_user(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get user's chats
    chats_query = text("""
        SELECT 
            c.id,
            c.created_at,
            c.updated_at,
            jsonb_array_length(c.history) as message_count,
            c.is_shared
        FROM chats c
        WHERE c.user_id = :user_id
        ORDER BY c.updated_at DESC
    """)
    
    result = await db.execute(chats_query, {"user_id": target_user_id})
    chats = result.fetchall()
    
    # Get user's preferences
    prefs_query = text("""
        SELECT * FROM user_preferences WHERE user_id = :user_id
    """)
    prefs_result = await db.execute(prefs_query, {"user_id": target_user_id})
    prefs = prefs_result.fetchone()
    
    return {
        "userId": target_user_id,
        "chats": [
            {
                "id": str(c[0]),
                "createdAt": c[1].isoformat() if c[1] else None,
                "updatedAt": c[2].isoformat() if c[2] else None,
                "messageCount": c[3],
                "isShared": c[4],
            }
            for c in chats
        ],
        "preferences": {
            "tone": prefs[1] if prefs else "balanced",
            "responseLength": prefs[2] if prefs else "adaptive",
            "expertiseLevel": prefs[3] if prefs else "auto",
            "humorLevel": prefs[4] if prefs else 0.5,
            "feedbackCount": prefs[5] if prefs else 0,
        } if prefs else None,
        "totalChats": len(chats),
    }