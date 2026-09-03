"""
Fix script to complete quests that have reached their goal but status is still active
Run: docker-compose exec bot python fix_completed_quests.py
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from bot.database.db import async_session
from bot.database.models import User, UserQuest, Quest
from bot.database.queries import add_exp, add_coins, add_inventory_item, update_location_progress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_completed_quests():
    """Check and complete quests that should be completed"""
    async with async_session() as session:
        # Get all active user quests
        result = await session.execute(
            select(UserQuest).where(UserQuest.status == "active")
        )
        active_quests = result.scalars().all()
        
        logger.info(f"Checking {len(active_quests)} active quests...")
        
        fixed_count = 0
        
        for uq in active_quests:
            # Load quest and user
            quest_result = await session.execute(select(Quest).where(Quest.id == uq.quest_id))
            quest = quest_result.scalar_one_or_none()
            
            if not quest:
                continue
            
            user_result = await session.execute(select(User).where(User.id == uq.user_id))
            user = user_result.scalar_one_or_none()
            
            if not user:
                continue
            
            should_complete = False
            
            # Check kill quest
            if quest.conditions.get("kill"):
                required_count = quest.conditions["kill"]["count"]
                current_killed = uq.progress.get("killed", 0) if uq.progress else 0
                
                if current_killed >= required_count:
                    # Check boss progress requirement
                    is_boss = getattr(quest, 'is_boss_quest', False)
                    if is_boss:
                        current_progress = user.location_progress.get(quest.location, 0)
                        if current_progress >= 70:
                            should_complete = True
                        else:
                            logger.info(f"Quest {quest.id} ({quest.title}) for user {user.telegram_id}: killed {current_killed}/{required_count} but boss requires 70% progress (current: {current_progress}%)")
                    else:
                        should_complete = True
            
            # Check collect quest
            if quest.conditions.get("collect"):
                required_count = quest.conditions["collect"]["count"]
                current_collected = uq.progress.get("collected", 0) if uq.progress else 0
                
                if current_collected >= required_count:
                    should_complete = True
            
            if should_complete:
                logger.info(f"Completing quest {quest.id} ({quest.title}) for user {user.telegram_id}")
                
                # Complete quest
                uq.status = "completed"
                uq.completed_at = datetime.utcnow()
                
                # Add rewards
                user = await add_exp(session, user, quest.reward_exp)
                user = await add_coins(session, user, quest.reward_coins)
                user.stars += quest.reward_stars
                
                for reward_item in quest.reward_items:
                    item_name = reward_item["item"]
                    quantity = reward_item["quantity"]
                    await add_inventory_item(session, user.id, item_name, "material", quantity)
                
                user = await update_location_progress(session, user, quest.location, quest.progress_reward)
                
                fixed_count += 1
                logger.info(f"✅ Completed quest for user {user.telegram_id}: +{quest.reward_exp} exp, +{quest.reward_coins} coins, +{quest.reward_stars} stars")
        
        await session.commit()
        logger.info(f"✅ Fixed {fixed_count} quests")


if __name__ == "__main__":
    asyncio.run(fix_completed_quests())
