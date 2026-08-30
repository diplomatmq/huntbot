from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from bot.database.db import async_session
from bot.database.queries import get_or_create_user, update_energy, get_species_for_user
from bot.keyboards.profile_kb import get_profile_keyboard, get_skills_keyboard
from bot.utils.retry import retry

router = Router()


@router.callback_query(F.data.startswith("profile_"))
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

        free_total = user.total_hunts_free or 0
        free_ok = user.successful_hunts_free or 0
        story_total = user.total_hunts_story or 0
        story_ok = user.successful_hunts_story or 0
        total_hunts = free_total + story_total
        successful_hunts = free_ok + story_ok
        success_rate = int(successful_hunts / total_hunts * 100) if total_hunts > 0 else 0
        free_rate = int(free_ok / free_total * 100) if free_total > 0 else 0
        story_rate = int(story_ok / story_total * 100) if story_total > 0 else 0

        exp_needed = user.level * user.level * 100
        profile_text = (
            f"👤 <b>Профиль охотника</b>\n\n"
            f"📊 Уровень: {user.level}\n"
            f"⭐ Опыт: {user.exp}/{exp_needed}\n\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}\n"
            f"💰 Монеты: {user.coins}\n"
            f"🌟 Звёзды: {user.stars}\n\n"
            f"📍 Локация: {user.current_location}\n"
            f"🎮 Режим: {'Свободный' if user.game_mode == 'free' else 'Сюжетный'}\n\n"
            f"<b>Навыки:</b>\n"
            f"{skills_text}\n\n"
            f"📈 Статистика:\n"
            f"• <b>Итого:</b> {total_hunts} охот, из них успешных {successful_hunts} ({success_rate}%)\n"
            f"• 🆓 Свободный: {free_total} охот, {free_ok} успешных ({free_rate}%)\n"
            f"• 📖 Сюжетный: {story_total} охот, {story_ok} успешных ({story_rate}%)"
        )

        try:
            await callback.message.edit_text(profile_text, reply_markup=get_profile_keyboard(callback.from_user.id))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("skills_"))
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

        try:
            await callback.message.edit_text(skills_text, reply_markup=get_skills_keyboard(callback.from_user.id, skill_points > 0))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("skill_"))
@retry(retry_count=3)
async def upgrade_skill(callback: CallbackQuery):
    skill_name = callback.data.split("_")[1]  # skill_accuracy_userId
    
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
    
    try:
        await callback.message.edit_text(skills_text, reply_markup=get_skills_keyboard(callback.from_user.id, skill_points > 0))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer(f"✅ {skill_name.capitalize()} улучшен!")


@router.callback_query(F.data.startswith("animals_"))
@retry(retry_count=3)
async def show_animals(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        
        species_data = await get_species_for_user(session, user.id)
        by_location = species_data["by_location"]
        total_kinds = species_data["kinds"]
        total_killed = species_data["killed"]
        
        # Location names in Russian
        location_names = {
            "forest": "🌲 Лес",
            "taiga": "🌲 Тайга",
            "mountains": "⛰️ Горы",
            "steppe": "🏜️ Степь",
            "desert": "🏜️ Пустыня",
            "jungle": "🌴 Джунгли",
            "swamp": "🐊 Болото",
            "tundra": "❄️ Тундра",
            "savanna": "🦁 Саванна",
            "rainforest": "🌧️ Тропический лес",
            "north_forest": "🌲 Северный лес",
            "deep_forest": "🌲 Глубокий лес",
            "ocean": "🌊 Океан",
            "volcano": "🌋 Вулкан"
        }
        
        text = f"🦌 <b>Животные</b>\n\n"
        text += f"Всего видов животных убито: <b>{total_kinds}</b> из возможных\n"
        text += f"Всего убито животных: <b>{total_killed}</b>\n\n"
        
        if by_location:
            for location_id, animals in sorted(by_location.items()):
                loc_name = location_names.get(location_id, location_id)
                text += f"<b>{loc_name}</b> ({len(animals)} видов):\n"
                for animal_name, count in sorted(animals):
                    text += f"  • {animal_name}: {count}\n"
                text += "\n"
        else:
            text += "Вы ещё не убили ни одного животного!"
        
        try:
            await callback.message.edit_text(text, reply_markup=get_profile_keyboard(callback.from_user.id))
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()
