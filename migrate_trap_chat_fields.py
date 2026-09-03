"""
Migration script to add trap_chat_id and trap_message_id fields to users table
Run this once: docker-compose exec bot python migrate_trap_chat_fields.py
"""
import asyncio
import logging
from sqlalchemy import text
from bot.database.db import async_session, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_trap_chat_fields():
    """Add trap_chat_id and trap_message_id columns to users table"""
    async with engine.begin() as conn:
        # Check if columns exist
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='users' AND column_name IN ('trap_chat_id', 'trap_message_id')
        """))
        existing_columns = {row[0] for row in result}
        
        if 'trap_chat_id' not in existing_columns:
            logger.info("Adding trap_chat_id column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN trap_chat_id BIGINT"))
            logger.info("✅ Added trap_chat_id column")
        else:
            logger.info("trap_chat_id column already exists")
        
        if 'trap_message_id' not in existing_columns:
            logger.info("Adding trap_message_id column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN trap_message_id BIGINT"))
            logger.info("✅ Added trap_message_id column")
        else:
            logger.info("trap_message_id column already exists")
    
    logger.info("✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_trap_chat_fields())
