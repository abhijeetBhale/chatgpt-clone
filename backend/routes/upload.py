from fastapi import APIRouter
from services.imagekit import get_upload_auth_params

router = APIRouter(tags=["upload"])


@router.get("/api/upload")
async def get_upload_auth():
    """Get ImageKit authentication parameters for client-side uploads."""
    return get_upload_auth_params()
