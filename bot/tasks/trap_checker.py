"""
Background task to check and trigger active traps
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User
from bot.config import BOT_TOKEN
from aiogram import Bot

logger = logging.getLogger(__name__)


async def check_active_traps(bot: Bot):
    """Check all active traps and trigger them if ready"""
    from bot.handlers.trap import TRAP_CONFIGS, trigger_trap_catch
    
    async with async_session() as session:
        # Find all users with active traps
        result = await session.execute(
            select(User).where(User.trap_active == True)
        )
        users = result.scalars().all()
        
        if not users:
            return
        
        logger.info(f"[TRAP_CHECKER] Checking {len(users)} active traps")
        
        for user in users:
            try:
                # Fix old users
                if user.trap_level == 0:
                    user.trap_level = 1
                    await session.commit()
                    await session.refresh(user)
                
                if not user.trap_set_time:
                    continue
                
                config = TRAP_CONFIGS[user.trap_level]
                trigger_time = user.trap_set_time + timedelta(minutes=config["trigger_time_min"])
                now = datetime.utcnow()
                
                if now >= trigger_time:
                    # Trigger trap!
                    logger.info(f"[TRAP_CHECKER] Triggering trap for user {user.telegram_id}")
                    trap_result = await trigger_trap_catch(user, session, config)
                    
                    if trap_result:
                        # Send results to user
                        await send_trap_results_to_user(bot, user.telegram_id, trap_result)
                        logger.info(f"[TRAP_CHECKER] Sent trap results to user {user.telegram_id}")
            except Exception as e:
                logger.error(f"[TRAP_CHECKER] Error processing trap for user {user.telegram_id}: {e}", exc_info=True)
                continue


async def send_trap_results_to_user(bot: Bot, telegram_id: int, trap_result: dict):
    """Send trap catch results to user via bot"""
    from bot.game_logic.animals import drop_to_ru
    
    num_animals = trap_result["num_animals"]
    caught_animals = trap_result["caught_animals"]
    total_exp = trap_result["total_exp"]
    total_coins = trap_result["total_coins"]
    all_drops = trap_result["all_drops"]
    location = trap_result["location"]
    user = trap_result["user"]
    
    rarity_emoji = {
        "common": "⚪",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡"
    }
    
    # Format animals list with weight and rarity
    animals_text = ""
    for i, catch in enumerate(caught_animals, 1):
        animal = catch["animal"]
        weight = catch["weight"]
        animals_text += f"{i}. {rarity_emoji.get(animal.rarity, '⚪')} {animal.emoji} {animal.name} ({weight} кг, {animal.rarity})\n"
    
    # Format drops
    drops_by_type = {}
    for item, quantity in all_drops.items():
        ru_name = drop_to_ru(item)
        if ru_name not in drops_by_type:
            drops_by_type[ru_name] = 0
        drops_by_type[ru_name] += quantity
    
    drops_lines = []
    for item_name, total_qty in sorted(drops_by_type.items()):
        drops_lines.append(f"• {total_qty}x {item_name}")
    drops_text = "\n".join(drops_lines) if drops_lines else "Нет добычи"
    
    from bot.handlers.trap import TRAP_CONFIGS
    config = TRAP_CONFIGS[user.trap_level]
    
    text = (
        f"🎉 <b>Ловушка сработала!</b>\n\n"
        f"{config['emoji']} <b>{config['name']}</b>\n"
        f"🦌 Поймано животных: {num_animals}\n\n"
        f"<b>Пойманные животные:</b>\n{animals_text}\n"
        f"📊 Общие награды:\n"
        f"• +{total_exp} опыта\n"
        f"• +{total_coins} монет\n\n"
        f"<b>Добыча:</b>\n{drops_text}\n\n"
        f"📍 Локация: {location.emoji} {location.name}\n"
        f"⚡ Энергия: {user.energy}/{user.max_energy}"
    )
    
    try:
        await bot.send_message(telegram_id, text)
    except Exception as e:
        logger.error(f"[TRAP_CHECKER] Failed to send message to {telegram_id}: {e}")


async def trap_checker_loop(bot: Bot):
    """Main loop for trap checker"""
    logger.info("[TRAP_CHECKER] Started trap checker background task")
    
    while True:
        try:
            await check_active_traps(bot)
        except Exception as e:
            logger.error(f"[TRAP_CHECKER] Error in trap checker loop: {e}", exc_info=True)
        
        # Check every 30 seconds
        await asyncio.sleep(30)
