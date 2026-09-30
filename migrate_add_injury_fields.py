"""
Migration script to add injury fields to User model
Run this once to add injured and injured_until fields
"""
import asyncio
from sqlalchemy import text
from bot.database.db import async_session, init_db


async def migrate():
    await init_db()
    
    async with async_session() as session:
        try:
            # Add injured column (Boolean, default False)
            await session.execute(text(
                "ALTER TABLE users ADD COLUMN injured BOOLEAN DEFAULT FALSE"
            ))
            print("✅ Added 'injured' column")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("⚠️  Column 'injured' already exists, skipping")
            else:
                print(f"❌ Error adding 'injured' column: {e}")
                raise
        
        try:
            # Add injured_until column (DateTime, nullable)
            await session.execute(text(
                "ALTER TABLE users ADD COLUMN injured_until TIMESTAMP"
            ))
            print("✅ Added 'injured_until' column")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("⚠️  Column 'injured_until' already exists, skipping")
            else:
                print(f"❌ Error adding 'injured_until' column: {e}")
                raise
        
        await session.commit()
        print("🎉 Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
