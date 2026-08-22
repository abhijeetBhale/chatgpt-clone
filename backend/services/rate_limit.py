"""Rate limiting service using slowapi with Redis backend."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def _get_client_identifier(request: Request) -> str:
    """Return per-user key if authenticated, else per-IP key.

    The Clerk user ID is extracted from the Authorization header by the
    auth middleware and stored on ``request.state.user_id``.  If absent
    (unauthenticated endpoint or malformed token) we fall back to the
    client IP address so that anonymous traffic is still throttled.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_get_client_identifier,
    default_limits=["100/minute"],
    storage_uri=None,  # set at startup from REDIS_URL
)
