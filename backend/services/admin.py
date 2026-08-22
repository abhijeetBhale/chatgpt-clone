"""Admin identification via Clerk emails listed in ADMIN_EMAILS.

Resolves the primary email for a Clerk user ID through the Clerk Backend
API and caches the result in-process to avoid a round trip per request.
"""
import logging
import time

import httpx
from fastapi import Depends, HTTPException, Request

from services.auth import get_current_user_id
from settings import settings

log = logging.getLogger("admin")

_EMAIL_CACHE: dict[str, tuple[str | None, float]] = {}
_TTL_SECONDS = 3600


def _allowed_emails() -> set[str]:
    return {
        e.strip().lower()
        for e in settings.ADMIN_EMAILS.split(",")
        if e.strip()
    }


async def _email_for_user(user_id: str) -> str | None:
    hit = _EMAIL_CACHE.get(user_id)
    if hit and time.time() - hit[1] < _TTL_SECONDS:
        return hit[0]

    email: str | None = None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"https://api.clerk.com/v1/users/{user_id}",
                headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
            )
        if resp.status_code == 200:
            data = resp.json()
            primary_id = data.get("primary_email_address_id")
            for entry in data.get("email_addresses", []):
                if entry.get("id") == primary_id:
                    email = entry.get("email_address")
                    break
    except Exception as e:
        log.warning("Clerk user lookup failed for %s: %s", user_id, e)

    _EMAIL_CACHE[user_id] = (email, time.time())
    return email


async def is_admin_user(user_id: str | None) -> bool:
    """True when the user's Clerk email is in ADMIN_EMAILS."""
    if not user_id:
        return False
    email = await _email_for_user(user_id)
    return bool(email and email.lower() in _allowed_emails())


async def get_admin_status(request: Request) -> bool:
    """Non-raising variant, for the frontend to show/hide admin UI."""
    return await is_admin_user(getattr(request.state, "user_id", None))


async def require_admin(
    request: Request,
    user_id: str = Depends(get_current_user_id),
) -> str:
    """Route dependency — rejects non-admins with 403."""
    if not await is_admin_user(user_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id
