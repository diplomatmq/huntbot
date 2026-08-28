from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.database.db import async_session
from bot.database.queries import get_or_create_user, update_energy
from bot.keyboards.profile_kb import get_profile_keyboard, get_skills_keyboard
from bot.utils.retry import retry

router = Router()


@router.callback_query(F.data == "profile")
@retry(retry_count=3)
async def show_profile(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)

        skills_text = (
            f"🎯 Меткость: {user.skills.get('accuracy', 0)} (+{user.skills.get('accuracy', 0) * 2}% к попаданию)\n"
            f"👻 Скрытность: {user.skills.get('stealth', 0)} (+{user.skills.get('stealth', 0) * 3}% к поиску следов)\n"
            f"💪 Выносливость: {user.skills.get('endurance', 0)} (+{user.skills.get('endurance', 0) * 2} макс. энергии)"
        )

        # Calculate statistics based on mode
        if user.game_mode == "free":
            total_hunts = user.total_hunts_free
            successful_hunts = user.successful_hunts_free
        else:
            total_hunts = user.total_hunts_story
            successful_hunts = user.successful_hunts_story

        success_rate = int(successful_hunts / total_hunts * 100) if total_hunts > 0 else 0

        profile_text = (
            f"👤 <b>Профиль охотника</b>\n\n"
            f"📊 Уровень: {user.level}\n"
            f"⭐ Опыт: {user.exp}/{user.level * 100}\n\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}\n"
            f"💰 Монеты: {user.coins}\n"
            f"🌟 Звёзды: {user.stars}\n\n"
            f"📍 Локация: {user.current_location}\n"
            f"🎮 Режим: {'Свободный' if user.game_mode == 'free' else 'Сюжетный'}\n\n"
            f"<b>Навыки:</b>\n"
            f"{skills_text}\n\n"
            f"📈 Статистика:\n"
            f"• Всего охот: {total_hunts}\n"
            f"• Успешных: {successful_hunts}\n"
            f"• Успешность: {success_rate}%"
        )

        await callback.message.edit_text(profile_text, reply_markup=get_profile_keyboard())
        await callback.answer()


@router.callback_query(F.data == "skills")
@retry(retry_count=3)
async def show_skills(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)

        skill_points = user.level - sum(user.skills.values())

        skills_text = (
            f"🎯 <b>Навыки</b>\n\n"
            f"Доступно очков: {skill_points}\n\n"
            f"🎯 Меткость ({user.skills.get('accuracy', 0)})\n"
            f"+2% к шансу попадания за уровень\n\n"
            f"👻 Скрытность ({user.skills.get('stealth', 0)})\n"
            f"+3% к шансу найти след за уровень\n\n"
            f"💪 Выносливость ({user.skills.get('endurance', 0)})\n"
            f"+2 макс. энергии и -1% затрат энергии за уровень"
        )

        await callback.message.edit_text(skills_text, reply_markup=get_skills_keyboard(skill_points > 0))
        await callback.answer()


@router.callback_query(F.data.startswith("skill_"))
@retry(retry_count=3)
async def upgrade_skill(callback: CallbackQuery):
    skill_name = callback.data.split("_")[1]
    
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        
        skill_points = user.level - sum(user.skills.values())
        if skill_points <= 0:
            await callback.answer("❌ Нет очков навыков!", show_alert=True)
            return
        
        # Increment the skill
        current_value = user.skills.get(skill_name, 0)
        user.skills[skill_name] = current_value + 1
        
        # Update max energy if endurance
        if skill_name == "endurance":
            from bot.game_logic.hunt_calculator import calculate_max_energy
            user.max_energy = calculate_max_energy(user.skills["endurance"])
        
        # Mark as modified for SQLAlchemy to detect JSON change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "skills")
        
        await session.commit()
        await session.refresh(user)
    
    # Recalculate skill points
    skill_points = user.level - sum(user.skills.values())
    
    skills_text = (
        f"🎯 <b>Навыки</b>\n\n"
        f"Доступно очков: {skill_points}\n\n"
        f"🎯 Меткость ({user.skills.get('accuracy', 0)})\n"
        f"+2% к шансу попадания за уровень\n\n"
        f"👻 Скрытность ({user.skills.get('stealth', 0)})\n"
        f"+3% к шансу найти след за уровень\n\n"
        f"💪 Выносливость ({user.skills.get('endurance', 0)})\n"
        f"+2 макс. энергии и -1% затрат энергии за уровень"
    )
    
    await callback.message.edit_text(skills_text, reply_markup=get_skills_keyboard(skill_points > 0))
    await callback.answer(f"✅ {skill_name.capitalize()} улучшен!")
