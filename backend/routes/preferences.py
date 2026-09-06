"""User Preferences API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import UserPreferenceRequest, UserPreferenceResponse
from services.auth import get_current_user_id
from services.personality import get_personality_engine
from services.learning import get_feedback_analyzer
from services.rate_limit import limiter
from services.plans import read_limit, mutate_limit

log = logging.getLogger("preferences")

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("")
@limiter.limit(read_limit)
async def get_preferences(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's personality preferences."""
    engine = get_personality_engine(db)
    prefs = await engine.get_user_preferences(user_id)
    
    return UserPreferenceResponse(
        user_id=prefs.user_id,
        tone=prefs.tone,
        response_length=prefs.response_length,
        expertise_level=prefs.expertise_level,
        humor_level=prefs.humor_level,
        feedback_count=prefs.feedback_count,
        created_at=prefs.created_at,
        updated_at=prefs.updated_at,
    ).to_frontend()


@router.put("")
@limiter.limit(mutate_limit)
async def update_preferences(
    request: Request,
    body: UserPreferenceRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's personality preferences."""
    engine = get_personality_engine(db)
    
    updates = {}
    if body.tone is not None:
        if body.tone not in ["formal", "casual", "enthusiastic", "minimal", "balanced"]:
            raise HTTPException(status_code=400, detail="Invalid tone value")
        updates["tone"] = body.tone
    
    if body.response_length is not None:
        if body.response_length not in ["concise", "detailed", "adaptive"]:
            raise HTTPException(status_code=400, detail="Invalid response_length value")
        updates["response_length"] = body.response_length
    
    if body.expertise_level is not None:
        if body.expertise_level not in ["beginner", "intermediate", "expert", "auto"]:
            raise HTTPException(status_code=400, detail="Invalid expertise_level value")
        updates["expertise_level"] = body.expertise_level
    
    if body.humor_level is not None:
        if not 0.0 <= body.humor_level <= 1.0:
            raise HTTPException(status_code=400, detail="humor_level must be between 0.0 and 1.0")
        updates["humor_level"] = body.humor_level
    
    prefs = await engine.update_user_preferences(user_id, updates)
    
    return {
        "status": "ok",
        "preferences": {
            "tone": prefs.tone,
            "responseLength": prefs.response_length,
            "expertiseLevel": prefs.expertise_level,
            "humorLevel": prefs.humor_level,
        }
    }


@router.get("/learning-summary")
@limiter.limit(read_limit)
async def get_learning_summary(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a summary of what has been learned about this user."""
    analyzer = get_feedback_analyzer(db)
    summary = await analyzer.get_user_learning_summary(user_id)
    return summary