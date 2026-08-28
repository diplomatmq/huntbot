from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.database.db import async_session
from bot.database.queries import get_or_create_user, update_energy
from bot.game_logic.locations import (
    get_location, get_all_locations, get_unlocked_locations, 
    can_unlock_location, is_boss_unlocked
)
from bot.keyboards.location_kb import get_locations_keyboard

router = Router()


@router.callback_query(F.data == "locations")
async def show_locations(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)

        unlocked = get_unlocked_locations(user.location_progress, user.game_mode)

        mode_text = "🆓 Свободный режим" if user.game_mode == "free" else "📖 Сюжетный режим"
        text = f"📍 <b>Локации</b> ({mode_text})\n\n"

        if user.game_mode == "free":
            text += "В свободном режиме все локации доступны!\n"
            text += "Выберите локацию для путешествия:\n\n"
        else:
            text += "В сюжетном режиме локации открываются по мере прохождения.\n"
            text += "Набирайте прогресс, чтобы открыть новые локации!\n\n"

        for loc in unlocked:
            progress = user.location_progress.get(loc.id, 0)
            is_current = loc.id == user.current_location
            boss_unlocked = is_boss_unlocked(loc.id, user.location_progress)

            status = "📍" if is_current else "🔓"
            
            if user.game_mode == "story":
                boss_status = "👹 Босс доступен!" if boss_unlocked else f"👹 Босс: {progress}%"
                text += f"{status} {loc.emoji} <b>{loc.name}</b>\n"
                text += f"   Прогресс: {progress}%\n"
                text += f"   {boss_status}\n\n"
            else:
                text += f"{status} {loc.emoji} <b>{loc.name}</b>\n"
                text += f"   {loc.description}\n\n"

        try:
            await callback.message.edit_text(text, reply_markup=get_locations_keyboard(unlocked))
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


@router.callback_query(F.data.startswith("travel_"))
async def travel_to_location(callback: CallbackQuery):
    location_id = callback.data.split("_")[1]
    
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user = await update_energy(session, user)
        
        if not can_unlock_location(location_id, user.location_progress, user.game_mode):
            await callback.answer("❌ Локация не разблокирована! Завершите предыдущую локацию в сюжетном режиме.", show_alert=True)
            return
        
        energy_cost = 5
        if user.energy < energy_cost:
            await callback.answer("❌ Недостаточно энергии для перехода!", show_alert=True)
            return
        
        from bot.database.queries import consume_energy
        if not await consume_energy(session, user, energy_cost):
            await callback.answer("❌ Недостаточно энергии!", show_alert=True)
            return
        
        user.current_location = location_id
        await session.commit()
        
        location = get_location(location_id)
    
    await callback.answer(f"🚀 Вы переместились в {location.name}!")
    
    # Refresh locations view
    unlocked = get_unlocked_locations(user.location_progress, user.game_mode)
    
    mode_text = "🆓 Свободный режим" if user.game_mode == "free" else "📖 Сюжетный режим"
    text = f"📍 <b>Локации</b> ({mode_text})\n\n"

    if user.game_mode == "free":
        text += "В свободном режиме все локации доступны!\n"
        text += "Выберите локацию для путешествия:\n\n"
    else:
        text += "В сюжетном режиме локации открываются по мере прохождения.\n"
        text += "Набирайте прогресс, чтобы открыть новые локации!\n\n"
    
    for loc in unlocked:
        progress = user.location_progress.get(loc.id, 0)
        is_current = loc.id == user.current_location
        boss_unlocked = is_boss_unlocked(loc.id, user.location_progress)
        
        status = "📍" if is_current else "🔓"
        
        if user.game_mode == "story":
            boss_status = "👹 Босс доступен!" if boss_unlocked else f"👹 Босс: {progress}%"
            text += f"{status} {loc.emoji} <b>{loc.name}</b>\n"
            text += f"   Прогресс: {progress}%\n"
            text += f"   {boss_status}\n\n"
        else:
            text += f"{status} {loc.emoji} <b>{loc.name}</b>\n"
            text += f"   {loc.description}\n\n"
    
    try:
        await callback.message.edit_text(text, reply_markup=get_locations_keyboard(unlocked))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
