from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from sqlalchemy import text

from database import engine, Base
from routes import api_router
from settings import settings
from services.cache import cache
from services.rate_limit import limiter
from services.plans import current_plan, plan_from_token
from services.auth import _decode_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize cache
    await cache.connect()

    # Attach Redis storage to the rate limiter now that Redis is up
    if settings.RATE_LIMIT_ENABLED and cache._connected and cache.redis_client:
        from slowapi.backends import RedisBackend
        limiter._storage = RedisBackend(cache.redis_client)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Run migrations for new columns
        migrations = [
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS feedback JSONB NOT NULL DEFAULT '{}'",
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS edit_history JSONB NOT NULL DEFAULT '[]'",
            "ALTER TABLE user_chats ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE feature_flags ALTER COLUMN updated_at SET DEFAULT now()",
        ]
        for migration in migrations:
            try:
                await conn.execute(text(migration))
            except Exception:
                pass  # Column already exists

        # Seed default feature flags (idempotent). New flags start OFF;
        # toggle them on from the Feature Flags page (/admin).
        seed_flags = [
            ("enable_chat_sharing", "Allow users to share chats via public link", False),
            ("show_pricing_page", "Show the Pricing page and its navbar tab", False),
        ]
        for name, description, enabled in seed_flags:
            await conn.execute(
                text(
                    "INSERT INTO feature_flags (name, description, enabled, updated_at) "
                    "VALUES (:n, :d, :e, now()) ON CONFLICT (name) DO NOTHING"
                ),
                {"n": name, "d": description, "e": enabled},
            )

    print("Database tables created and migrated")
    yield

    # Cleanup
    await cache.disconnect()
    await engine.dispose()


app = FastAPI(
    title="Boost AI Backend",
    description="AI Chat Backend API",
    version="2.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.CLIENT_URL,
        "http://localhost:5173",
        "https://chatgpt-clone-production.up.railway.app",
        "https://boost-ai-chat.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach slowapi limiter to the app state
app.state.limiter = limiter


# ---------------------------------------------------------------------------
# Middleware: extract user_id from JWT and store on request.state
# This lets the rate-limiter key function use the user ID instead of IP.
# ---------------------------------------------------------------------------
@app.middleware("http")
async def extract_user_id_middleware(request: Request, call_next):
    request.state.user_id = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = _decode_token(token)
            request.state.user_id = payload.get("sub")
            request.state.plan = plan_from_token(payload)
            current_plan.set(request.state.plan)
        except Exception:
            pass  # invalid token — rate limiter will fall back to IP
    response = await call_next(request)
    return response


# ---------------------------------------------------------------------------
# Rate-limit exceeded handler (returns JSON instead of plain text)
# ---------------------------------------------------------------------------
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": getattr(exc, "retry_after", None),
        },
    )


def _verify_docs_auth(request: Request):
    from services.auth import _decode_token as _dt
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        _dt(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/docs", include_in_schema=False)
async def protected_swagger_ui(request: Request):
    _verify_docs_auth(request)
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Boost AI Docs")


@app.get("/redoc", include_in_schema=False)
async def protected_redoc(request: Request):
    _verify_docs_auth(request)
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(openapi_url="/openapi.json", title="Boost AI Docs")


@app.get("/openapi.json", include_in_schema=False)
async def protected_openapi(request: Request):
    _verify_docs_auth(request)
    return app.openapi()


app.include_router(api_router)


@app.get("/")
async def health_check():
    return {
        "message": "AI Chat Backend is running!",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.1.0 (Python/FastAPI)",
    }
