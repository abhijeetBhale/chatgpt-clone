import base64

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from settings import settings

security = HTTPBearer()


def _issuer_from_publishable_key(key: str) -> str:
    """Derive the Clerk Frontend API URL (JWT issuer) from a publishable key."""
    if not key or not key.startswith("pk_"):
        raise RuntimeError("CLERK_PUBLISHABLE_KEY must be set to verify auth tokens")
    encoded = key.split("_", 2)[2]
    padded = encoded + "=" * (-len(encoded) % 4)
    domain = base64.urlsafe_b64decode(padded).decode("utf-8").rstrip("$")
    if not domain:
        raise RuntimeError("Could not derive Frontend API URL from CLERK_PUBLISHABLE_KEY")
    return f"https://{domain}"


_CLERK_ISSUER = (
    settings.CLERK_ISSUER_URL
    or _issuer_from_publishable_key(settings.CLERK_PUBLISHABLE_KEY)
)

# Fetches Clerk's public signing keys and caches them (refreshed automatically).
_jwks_client = PyJWKClient(f"{_CLERK_ISSUER}/.well-known/jwks.json", cache_keys=True)


def _decode_token(token: str) -> dict:
    """Decode and cryptographically verify a Clerk session JWT."""
    signing_key = _jwks_client.get_signing_key_from_jwt(token).key
    return jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        issuer=_CLERK_ISSUER,
        options={"verify_aud": False},
    )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verify Clerk JWT signature/expiry and return the user ID."""
    token = credentials.credentials

    try:
        payload = _decode_token(token)
        return payload["sub"]
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
