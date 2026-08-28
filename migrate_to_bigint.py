"""
Migration script to change INTEGER columns to BIGINT for Telegram IDs and chat IDs.
This fixes the "value out of int32 range" error.
"""
import asyncio
from sqlalchemy import text
from bot.database.db import engine


async def migrate_to_bigint():
    """Alter columns from INTEGER to BIGINT to support large Telegram IDs"""
    
    async with engine.begin() as conn:
        # Alter users.telegram_id
        print("Altering users.telegram_id to BIGINT...")
        await conn.execute(text("""
            ALTER TABLE users 
            ALTER COLUMN telegram_id TYPE BIGINT
        """))
        print("✅ users.telegram_id migrated to BIGINT")
        
        # Alter stars_transactions.message_id
        print("Altering stars_transactions.message_id to BIGINT...")
        await conn.execute(text("""
            ALTER TABLE stars_transactions 
            ALTER COLUMN message_id TYPE BIGINT
        """))
        print("✅ stars_transactions.message_id migrated to BIGINT")
        
        # Alter stars_transactions.chat_id
        print("Altering stars_transactions.chat_id to BIGINT...")
        await conn.execute(text("""
            ALTER TABLE stars_transactions 
            ALTER COLUMN chat_id TYPE BIGINT
        """))
        print("✅ stars_transactions.chat_id migrated to BIGINT")
        
        await conn.commit()
        print("\n🎉 Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_to_bigint())
