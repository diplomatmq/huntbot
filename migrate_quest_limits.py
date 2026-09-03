"""
Migration script to limit active quests:
- 1 main (story) quest per location
- 2 side quests total
"""
import asyncio
import logging
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User, UserQuest, Quest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_quest_limits():
    """Limit active quests per user, preserving progress"""
    async with async_session() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        logger.info(f"Processing {len(users)} users...")
        
        total_modified = 0
        
        for user in users:
            # Get all active quests for this user
            quest_result = await session.execute(
                select(UserQuest).where(
                    UserQuest.user_id == user.id,
                    UserQuest.status == "active"
                ).join(Quest)
            )
            active_quests = quest_result.scalars().all()
            
            if not active_quests:
                continue
            
            # Separate by type
            main_quests = []
            side_quests = []
            
            for uq in active_quests:
                quest_result = await session.execute(
                    select(Quest).where(Quest.id == uq.quest_id)
                )
                quest = quest_result.scalar_one_or_none()
                
                if quest:
                    if quest.quest_type == "main":
                        main_quests.append((uq, quest))
                    else:
                        side_quests.append((uq, quest))
            
            modified = False
            
            # Keep only 1 main quest (first one by location, then by started_at)
            if len(main_quests) > 1:
                # Sort by location, then by started_at
                main_quests.sort(key=lambda x: (x[1].location, x[0].started_at))
                keep_main = main_quests[0]
                
                for uq, quest in main_quests[1:]:
                    logger.info(f"User {user.telegram_id}: Pausing main quest '{quest.title}' (progress preserved)")
                    uq.status = "paused"  # New status to preserve progress
                    modified = True
            
            # Keep only 2 side quests (first two by started_at)
            if len(side_quests) > 2:
                side_quests.sort(key=lambda x: x[0].started_at)
                
                for uq, quest in side_quests[2:]:
                    logger.info(f"User {user.telegram_id}: Pausing side quest '{quest.title}' (progress preserved)")
                    uq.status = "paused"
                    modified = True
            
            if modified:
                total_modified += 1
        
        await session.commit()
        logger.info(f"Migration completed. Modified {total_modified} users.")


if __name__ == "__main__":
    asyncio.run(migrate_quest_limits())
