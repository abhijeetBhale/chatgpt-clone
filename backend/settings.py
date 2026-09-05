from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str = ""
    # Optional explicit override, e.g. https://powerful-stud-79.clerk.accounts.dev
    CLERK_ISSUER_URL: str = ""
    IMAGEKIT_URL_PUBLIC_KEY: str
    IMAGEKIT_URL_PRIVATE_KEY: str
    IMAGEKIT_URL_ENDPOINT: str
    CLIENT_URL: str = "http://localhost:5173"

    # Admins (comma-separated Clerk emails and/or user IDs)
    ADMIN_EMAILS: str = "abhijeetbhale7@gmail.com"

    # Multi-provider LLM keys (optional — enables failover)
    OPENROUTER_API_KEY: str = ""
    CEREBRAS_API_KEY: str = ""

    # Redis Cache Settings
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 300  # 5 minutes default
    CACHE_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AI: str = "10/minute"
    RATE_LIMIT_READ: str = "60/minute"
    RATE_LIMIT_MUTATE: str = "30/minute"
    RATE_LIMIT_GLOBAL: str = "100/minute"

    # Plans / Billing (Clerk Billing). Free tier uses the values above;
    # users subscribed to PRO_PLAN_SLUG get the PRO_* limits instead.
    PRO_PLAN_SLUG: str = "pro"
    PRO_RATE_LIMIT_AI: str = "40/minute"
    PRO_RATE_LIMIT_READ: str = "240/minute"
    PRO_RATE_LIMIT_MUTATE: str = "120/minute"
    PRO_RATE_LIMIT_GLOBAL: str = "400/minute"

    # File size limits per plan (in bytes)
    FREE_MAX_FILE_SIZE: int = 2 * 1024 * 1024   # 2 MB
    PRO_MAX_FILE_SIZE: int = 20 * 1024 * 1024    # 20 MB

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
