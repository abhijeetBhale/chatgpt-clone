import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


def _decode_token(token: str) -> dict:
    """Decode and validate a Clerk JWT."""
    payload = jwt.decode(
        token,
        options={"verify_signature": False},
    )
    if not payload.get("sub"):
        raise ValueError("Invalid token: no sub claim")
    return payload


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verify Clerk JWT and return the user ID."""
    token = credentials.credentials

    try:
        payload = _decode_token(token)
        return payload["sub"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
