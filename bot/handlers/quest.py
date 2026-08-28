from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.database.db import async_session
from bot.database.queries import get_or_create_user, update_energy, get_active_quests, get_available_quests
from bot.keyboards.quest_kb import get_quests_keyboard

router = Router()


@router.callback_query(F.data.startswith("quests_"))
async def show_quests(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)

        if user.game_mode != "story":
            await callback.answer("❌ Квесты доступны только в сюжетном режиме!", show_alert=True)
            return

        active_quests = await get_active_quests(session, user.id)
        available_quests = await get_available_quests(session, user.level, user.current_location)

        text = "📜 <b>Квесты</b>\n\n"

        if active_quests:
            text += "<b>Активные квесты:</b>\n"
            for uq in active_quests:
                quest = uq.quest
                progress_text = ""
                if quest.conditions.get("kill"):
                    target = quest.conditions["kill"]["animal"]
                    needed = quest.conditions["kill"]["count"]
                    current = uq.progress.get("killed", 0)
                    progress_text = f"Убито {current}/{needed} {target}"
                elif quest.conditions.get("collect"):
                    target = quest.conditions["collect"]["item"]
                    needed = quest.conditions["collect"]["count"]
                    current = uq.progress.get("collected", 0)
                    progress_text = f"Собрано {current}/{needed} {target}"

                quest_type = "📖 Сюжет" if quest.quest_type == "main" else "📋 Побочный"
                text += f"\n{quest_type} • {quest.title}\n"
                text += f"   {progress_text}\n"
        else:
            text += "<b>Активные квесты:</b>\nНет активных квестов\n"

        text += "\n"

        if available_quests:
            text += f"<b>Доступные квесты ({len(available_quests)}):</b>\n"
            for quest in available_quests[:5]:  # Show first 5
                quest_type = "📖 Сюжет" if quest.quest_type == "main" else "📋 Побочный"
                reward = f"+{quest.reward_exp} опыта, +{quest.reward_coins} монет"
                text += f"\n{quest_type} • {quest.title}\n"
                text += f"   Награда: {reward}\n"
        else:
            text += "<b>Доступные квесты:</b>\nНет доступных квестов\n"

        try:
            await callback.message.edit_text(text, reply_markup=get_quests_keyboard(callback.from_user.id))
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("take_quest_"))
async def take_quest(callback: CallbackQuery):
    quest_id = int(callback.data.split("_")[2])  # take_quest_id_userId
    
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        
        if user.game_mode != "story":
            await callback.answer("❌ Квесты доступны только в сюжетном режиме!", show_alert=True)
            return
        
        from bot.database.models import UserQuest, Quest
        from sqlalchemy import select
        
        # Check if already taken
        result = await session.execute(
            select(UserQuest).where(
                UserQuest.user_id == user.id,
                UserQuest.quest_id == quest_id,
                UserQuest.status == "active"
            )
        )
        if result.scalar_one_or_none():
            await callback.answer("❌ Квест уже взят!", show_alert=True)
            return
        
        # Get quest
        result = await session.execute(select(Quest).where(Quest.id == quest_id))
        quest = result.scalar_one_or_none()
        
        if not quest:
            await callback.answer("❌ Квест не найден!", show_alert=True)
            return
        
        # Create user quest
        user_quest = UserQuest(
            user_id=user.id,
            quest_id=quest_id,
            status="active",
            progress={}
        )
        session.add(user_quest)
        await session.commit()
    
    await callback.answer(f"✅ Квест «{quest.title}» взят!")
    await show_quests(callback)
