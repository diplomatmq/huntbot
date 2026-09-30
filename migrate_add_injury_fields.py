"""
Migration script to add injury fields to User model
Run this once to add injured and injured_until fields
"""
import asyncio
from sqlalchemy import text
from bot.database.db import async_session, init_db


async def column_exists(session, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    result = await session.execute(text(
        """
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        )
        """
    ), {"table_name": table_name, "column_name": column_name})
    return result.scalar()


async def migrate():
    await init_db()
    
    # Add injured column
    async with async_session() as session:
        if not await column_exists(session, "users", "injured"):
            await session.execute(text(
                "ALTER TABLE users ADD COLUMN injured BOOLEAN DEFAULT FALSE"
            ))
            await session.commit()
            print("✅ Added 'injured' column")
        else:
            print("⚠️  Column 'injured' already exists, skipping")
    
    # Add injured_until column (separate transaction)
    async with async_session() as session:
        if not await column_exists(session, "users", "injured_until"):
            await session.execute(text(
                "ALTER TABLE users ADD COLUMN injured_until TIMESTAMP"
            ))
            await session.commit()
            print("✅ Added 'injured_until' column")
        else:
            print("⚠️  Column 'injured_until' already exists, skipping")
    
    print("🎉 Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
