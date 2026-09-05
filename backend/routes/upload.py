from fastapi import APIRouter, Request
from services.imagekit import get_upload_auth_params
from services.plans import max_file_size, current_plan, FREE, PRO

router = APIRouter(tags=["upload"])


@router.get("/api/upload")
async def get_upload_auth():
    """Get ImageKit authentication parameters for client-side uploads."""
    return get_upload_auth_params()


@router.get("/api/upload/config")
async def get_upload_config(request: Request):
    """Get upload configuration based on user's plan."""
    plan = current_plan.get()
    return {
        "plan": plan,
        "maxFileSize": max_file_size(),
        "maxFileSizeMB": round(max_file_size() / (1024 * 1024), 1),
    }
