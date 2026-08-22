"""Feature flag service backed by Postgres with an in-memory TTL cache.

Usage in any route (the if/else logic):

    if await flags.is_enabled(db, "enable_chat_sharing"):
        ...
    else:
        raise HTTPException(403, "Feature disabled")
"""
import logging
import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import FeatureFlag

log = logging.getLogger("flags")

_CACHE: dict[str, tuple[bool, float]] = {}
_TTL_SECONDS = 15


def _cached(name: str) -> Optional[bool]:
    hit = _CACHE.get(name)
    if not hit:
        return None
    enabled, at = hit
    if time.time() - at > _TTL_SECONDS:
        return None
    return enabled


def invalidate(name: Optional[str] = None) -> None:
    """Drop cached value(s) after an admin toggles a flag."""
    if name is None:
        _CACHE.clear()
    else:
        _CACHE.pop(name, None)


async def list_flags(db: AsyncSession) -> list[FeatureFlag]:
    result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.name))
    return list(result.scalars().all())


async def get_flag(db: AsyncSession, name: str) -> Optional[FeatureFlag]:
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.name == name))
    return result.scalar_one_or_none()


async def is_enabled(db: AsyncSession, name: str) -> bool:
    """Unknown flags evaluate to False (fail closed)."""
    cached = _cached(name)
    if cached is not None:
        return cached

    flag = await get_flag(db, name)
    enabled = bool(flag and flag.enabled)
    _CACHE[name] = (enabled, time.time())
    return enabled
