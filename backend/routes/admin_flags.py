"""Admin routes for managing feature flags, plus a public read endpoint."""
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import FeatureFlag
from services import flags
from services.admin import get_admin_status, require_admin

router = APIRouter(prefix="/api", tags=["feature-flags"])

_NAME_RE = re.compile(r"^[a-z0-9_]{2,64}$")


class FlagCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    description: str = Field(default="", max_length=500)


class FlagToggle(BaseModel):
    enabled: bool


def _serialize(flag: FeatureFlag) -> dict:
    return {
        "name": flag.name,
        "description": flag.description,
        "enabled": flag.enabled,
        "updated_at": flag.updated_at.isoformat() if flag.updated_at else None,
    }


# --- Admin-only -----------------------------------------------------------


@router.get("/admin/session")
async def admin_session(is_admin: bool = Depends(get_admin_status)):
    """Lets the frontend decide whether to show admin UI."""
    return {"is_admin": is_admin}


@router.get("/admin/flags")
async def list_flags(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    rows = await flags.list_flags(db)
    return [_serialize(f) for f in rows]


@router.post("/admin/flags", status_code=201)
async def create_flag(
    body: FlagCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    name = body.name.strip().lower()
    if not _NAME_RE.match(name):
        raise HTTPException(
            status_code=422,
            detail="Flag name must be 2-64 chars: lowercase letters, digits, underscores",
        )
    if await flags.get_flag(db, name):
        raise HTTPException(status_code=409, detail=f"Flag '{name}' already exists")

    flag = FeatureFlag(name=name, description=body.description.strip(), enabled=False)
    db.add(flag)
    await db.flush()
    flags.invalidate()
    return _serialize(flag)


@router.patch("/admin/flags/{name}")
async def toggle_flag(
    name: str,
    body: FlagToggle,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    flag = await flags.get_flag(db, name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{name}' not found")

    flag.enabled = body.enabled
    await db.flush()
    flags.invalidate(name)
    log_line = f"'{name}' -> {'ON' if body.enabled else 'OFF'}"
    print(f"[admin] feature flag toggled: {log_line}")
    return _serialize(flag)


@router.delete("/admin/flags/{name}", status_code=204)
async def delete_flag(
    name: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    flag = await flags.get_flag(db, name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{name}' not found")
    await db.delete(flag)
    flags.invalidate(name)


# --- Public ----------------------------------------------------------------


@router.get("/flags")
async def public_flags(db: AsyncSession = Depends(get_db)):
    """Boolean map for client-side if/else logic. Safe to expose publicly."""
    rows = await flags.list_flags(db)
    return {f.name: f.enabled for f in rows}


# --- Pricing plan model (admin view) ---------------------------------------


def _parse_limit(raw: str) -> dict:
    value, _, period = raw.partition("/")
    return {"value": int(value), "period": period or "minute"}


@router.get("/admin/plans")
async def get_plan_model(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    """The configured pricing model — Free vs Pro tiers and their limits."""
    from settings import settings

    categories = {
        "AI messages": ("RATE_LIMIT_AI", "PRO_RATE_LIMIT_AI"),
        "Data reads": ("RATE_LIMIT_READ", "PRO_RATE_LIMIT_READ"),
        "Edits & shares": ("RATE_LIMIT_MUTATE", "PRO_RATE_LIMIT_MUTATE"),
    }
    rows = [
        {
            "feature": label,
            "free": _parse_limit(getattr(settings, free_key)),
            "pro": _parse_limit(getattr(settings, pro_key)),
        }
        for label, (free_key, pro_key) in categories.items()
    ]
    return {
        "pro_plan_slug": settings.PRO_PLAN_SLUG,
        "plans_are_managed_in_clerk_dashboard": True,
        "pricing_page_enabled": await flags.is_enabled(db, "show_pricing_page"),
        "rows": rows,
    }
