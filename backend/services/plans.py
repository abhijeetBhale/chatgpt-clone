"""Plan detection and per-plan rate-limit resolution.

Clerk Billing encodes the user's active subscription plan in the session
token's ``pla`` claim (e.g. ``u:pro`` for a user-level "pro" plan). The
middleware in main.py resolves the plan for every request and stores it on
``request.state.plan`` plus a contextvar; the slowapi limit providers below
read it at request time to select the matching limits.
"""
from contextvars import ContextVar

from settings import settings

FREE = "free"
PRO = "pro"

# Request-scoped plan, set by the auth middleware before routing.
current_plan: ContextVar[str] = ContextVar("current_plan", default=FREE)


def plan_from_token(payload: dict) -> str:
    """Resolve the plan from a verified Clerk session token payload."""
    raw = payload.get("pla")
    if not raw:
        return FREE
    # ``pla`` is 'scope:slug' (e.g. 'u:pro'); tolerate comma-joined lists.
    slugs = {part.strip().rsplit(":", 1)[-1] for part in str(raw).split(",")}
    return PRO if settings.PRO_PLAN_SLUG in slugs else FREE


def _limit(free_value: str, pro_value: str) -> str:
    return pro_value if current_plan.get() == PRO else free_value


def ai_limit() -> str:
    """slowapi limit provider: AI endpoints (create chat, send message)."""
    return _limit(settings.RATE_LIMIT_AI, settings.PRO_RATE_LIMIT_AI)


def read_limit() -> str:
    """slowapi limit provider: read-only endpoints."""
    return _limit(settings.RATE_LIMIT_READ, settings.PRO_RATE_LIMIT_READ)


def mutate_limit() -> str:
    """slowapi limit provider: mutation endpoints (edit, share, feedback)."""
    return _limit(settings.RATE_LIMIT_MUTATE, settings.PRO_RATE_LIMIT_MUTATE)


def global_limit() -> str:
    """slowapi limit provider: global default for undecorated routes."""
    return _limit(settings.RATE_LIMIT_GLOBAL, settings.PRO_RATE_LIMIT_GLOBAL)


def max_file_size() -> int:
    """Return the maximum upload file size in bytes for the current plan."""
    return settings.PRO_MAX_FILE_SIZE if current_plan.get() == PRO else settings.FREE_MAX_FILE_SIZE
