from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    CLERK_SECRET_KEY: str
    CLERK_PUBLISHABLE_KEY: str = ""
    IMAGEKIT_URL_PUBLIC_KEY: str
    IMAGEKIT_URL_PRIVATE_KEY: str
    IMAGEKIT_URL_ENDPOINT: str
    CLIENT_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
