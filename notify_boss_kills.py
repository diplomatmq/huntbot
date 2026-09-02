"""
Скрипт для отправки уведомлений игрокам, которые уже убили легендарных животных.
Запускается один раз для уведомления о победе над боссами.
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import HuntLog, User
from bot.config import BOT_TOKEN
from aiogram import Bot


async def notify_boss_kills():
    """Отправить уведомления всем, кто убил легендарных животных"""
    bot = Bot(token=BOT_TOKEN)
    
    async with async_session() as session:
        # Найти все успешные охоты на легендарных животных
        result = await session.execute(
            select(HuntLog).where(
                HuntLog.rarity == "legendary",
                HuntLog.is_successful == True
            )
        )
        legendary_kills = result.scalars().all()
        
        # Группируем по пользователям
        user_kills = {}
        for kill in legendary_kills:
            if kill.user_id not in user_kills:
                user_kills[kill.user_id] = []
            user_kills[kill.user_id].append(kill)
        
        print(f"Найдено {len(user_kills)} пользователей с легендарными убийствами")
        
        # Для каждого пользователя отправляем уведомление
        notified_count = 0
        for user_id, kills in user_kills.items():
            # Получаем пользователя
            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                print(f"Пользователь {user_id} не найден")
                continue
            
            # Формируем список убитых боссов
            bosses = []
            for kill in kills:
                bosses.append(f"{kill.animal_emoji} {kill.animal_name}")
            
            # Убираем дубликаты
            bosses = list(set(bosses))
            
            # Формируем сообщение
            message = (
                f"👑 <b>Уведомление о победе над боссами!</b>\n\n"
                f"Вы уже одолели следующих легендарных животных:\n"
            )
            for boss in bosses:
                message += f"🏆 {boss}\n"
            
            message += (
                f"\n"
                f"Отличная работа, охотник! Продолжайте покорять локации!"
            )
            
            try:
                await bot.send_message(user.telegram_id, message)
                print(f"Отправлено уведомление пользователю {user.telegram_id} (@{user.username})")
                notified_count += 1
                await asyncio.sleep(0.5)  # Небольшая задержка, чтобы не спамить
            except Exception as e:
                print(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
        
        print(f"\nВсего отправлено уведомлений: {notified_count}/{len(user_kills)}")
    
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(notify_boss_kills())
