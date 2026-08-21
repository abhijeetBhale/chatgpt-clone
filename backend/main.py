from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from sqlalchemy import text

from database import engine, Base
from routes import api_router
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Run migrations for new columns
        migrations = [
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS feedback JSONB NOT NULL DEFAULT '{}'",
            "ALTER TABLE chats ADD COLUMN IF NOT EXISTS edit_history JSONB NOT NULL DEFAULT '[]'",
            "ALTER TABLE user_chats ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT FALSE",
        ]
        for migration in migrations:
            try:
                await conn.execute(text(migration))
            except Exception:
                pass  # Column already exists
        
    print("Database tables created and migrated")
    yield
    await engine.dispose()


app = FastAPI(
    title="Boost AI Backend",
    description="AI Chat Backend API",
    version="2.0.0",
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


def _verify_docs_auth(request: Request):
    from services.auth import _decode_token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        _decode_token(token)
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
        "version": "2.0.0 (Python/FastAPI)",
    }
