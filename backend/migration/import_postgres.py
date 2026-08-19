"""Import exported MongoDB data into PostgreSQL."""
import json
import os
import uuid
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")


def parse_datetime(dt_str: str) -> datetime:
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        dt_str = dt_str.rstrip("Z")
        if "+" not in dt_str and "-" not in dt_str[10:]:
            dt_str += "+00:00"
        return datetime.fromisoformat(dt_str)
    except Exception:
        return datetime.now(timezone.utc)


async def import_data():
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    with open(os.path.join(EXPORT_DIR, "chats.json")) as f:
        chats_data = json.load(f)

    with open(os.path.join(EXPORT_DIR, "userchats.json")) as f:
        userchats_data = json.load(f)

    mongo_to_pg: dict[str, uuid.UUID] = {}

    async with async_session() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS chats (
                id UUID PRIMARY KEY,
                user_id TEXT NOT NULL,
                history JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await session.execute(text("CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id)"))

        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_chats (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_chats_user_id ON user_chats(user_id)"))

        for chat in chats_data:
            old_id = chat["_id"]
            new_id = uuid.uuid4()
            mongo_to_pg[old_id] = new_id

            await session.execute(
                text("""
                    INSERT INTO chats (id, user_id, history, created_at, updated_at)
                    VALUES (:id, :user_id, :history, :created_at, :updated_at)
                """),
                {
                    "id": new_id,
                    "user_id": chat.get("userId", ""),
                    "history": json.dumps(chat.get("history", [])),
                    "created_at": parse_datetime(str(chat.get("createdAt", ""))),
                    "updated_at": parse_datetime(str(chat.get("updatedAt", ""))),
                }
            )

        print(f"Imported {len(chats_data)} chats")

        userchat_count = 0
        for uc in userchats_data:
            user_id = uc.get("userId", "")
            for chat_entry in uc.get("chats", []):
                old_chat_id = chat_entry.get("_id", "")
                new_chat_id = mongo_to_pg.get(old_chat_id)
                if not new_chat_id:
                    print(f"Warning: No mapping found for chat_id {old_chat_id}, skipping")
                    continue

                created_at = parse_datetime(str(chat_entry.get("createdAt", "")))

                await session.execute(
                    text("""
                        INSERT INTO user_chats (user_id, chat_id, title, created_at, updated_at)
                        VALUES (:user_id, :chat_id, :title, :created_at, :updated_at)
                    """),
                    {
                        "user_id": user_id,
                        "chat_id": new_chat_id,
                        "title": chat_entry.get("title", "Untitled"),
                        "created_at": created_at,
                        "updated_at": created_at,
                    }
                )
                userchat_count += 1

        print(f"Imported {userchat_count} user chat entries")

        await session.commit()

    await engine.dispose()
    print("Import complete!")


if __name__ == "__main__":
    asyncio.run(import_data())
