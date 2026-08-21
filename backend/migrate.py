"""Migration script to add new columns to existing tables."""
import asyncio
from sqlalchemy import text
from database import engine


async def migrate():
    async with engine.begin() as conn:
        # Add is_shared column to chats table
        try:
            await conn.execute(text(
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            print("Added is_shared column to chats table")
        except Exception as e:
            print(f"Error adding is_shared to chats: {e}")

        # Add feedback column to chats table
        try:
            await conn.execute(text(
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS feedback JSONB NOT NULL DEFAULT '{}'"
            ))
            print("Added feedback column to chats table")
        except Exception as e:
            print(f"Error adding feedback to chats: {e}")

        # Add edit_history column to chats table
        try:
            await conn.execute(text(
                "ALTER TABLE chats ADD COLUMN IF NOT EXISTS edit_history JSONB NOT NULL DEFAULT '[]'"
            ))
            print("Added edit_history column to chats table")
        except Exception as e:
            print(f"Error adding edit_history to chats: {e}")

        # Add is_shared column to user_chats table
        try:
            await conn.execute(text(
                "ALTER TABLE user_chats ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            print("Added is_shared column to user_chats table")
        except Exception as e:
            print(f"Error adding is_shared to user_chats: {e}")

    print("Migration completed!")


if __name__ == "__main__":
    asyncio.run(migrate())
