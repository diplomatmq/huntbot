from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.database.db import async_session
from bot.database.queries import get_or_create_user, get_top_players_by_level
from bot.game_logic.locations import get_location
from bot.utils.retry import retry

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        location = get_location(user.current_location)
        mode_text = "Свободный режим" if user.game_mode == "free" else "Сюжетный режим"

        await message.answer(
            f"🦌 <b>Добро пожаловать в игру «Охота»!</b>\n\n"
            f"Вы — охотник, нанятый лесной службой для регулирования популяции хищников.\n"
            f"Исследуйте локации, выполняйте квесты, прокачивайте навыки и станьте легендарным охотником!\n\n"
            f"🎮 Режим: {mode_text}\n"
            f"📍 Текущая локация: {location.emoji} {location.name}\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}\n"
            f"💰 Монеты: {user.coins}\n"
            f"⭐ Звёзды: {user.stars}\n"
            f"📊 Уровень: {user.level}",
            reply_markup=get_main_menu_keyboard(user.telegram_id, user.game_mode),
            reply_to_message_id=message.message_id
        )


def _is_menu_hant_command(text: str) -> bool:
    if not text:
        return False
    t = text.strip().lower().replace("ё", "е")
    tokens = t.split()[:2]
    if len(tokens) < 2:
        return False
    return tokens[0] in {"хант", "hant", "охота", "hunt"} and tokens[1] in {"меню", "menu"}


@router.message(lambda msg: _is_menu_hant_command(msg.text or ""))
async def cmd_menu(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        location = get_location(user.current_location)
        mode_text = "Свободный режим" if user.game_mode == "free" else "Сюжетный режим"

        await message.answer(
            f"🦌 <b>Главное меню</b>\n\n"
            f"🎮 Режим: {mode_text}\n"
            f"📍 Текущая локация: {location.emoji} {location.name}\n"
            f"⚡ Энергия: {user.energy}/{user.max_energy}\n"
            f"💰 Монеты: {user.coins}\n"
            f"⭐ Звёзды: {user.stars}\n"
            f"📊 Уровень: {user.level}",
            reply_markup=get_main_menu_keyboard(user.telegram_id, user.game_mode),
            reply_to_message_id=message.message_id
        )


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>Справка по игре «Охота»</b>\n\n"
        "<b>Команды в чате:</b>\n"
        "• <code>хант меню</code> / <code>hunt menu</code> — Открыть главное меню\n"
        "• <code>хант</code> или <code>выстрел</code> — Охотиться (5 энергии)\n"
        "• <code>след</code> — Найти следы (+20% шанс редкого животного, 3 энергии)\n"
        "• <code>приманка</code> — Выбрать и установить приманку (4 энергии)\n"
        "• <code>засада</code> — Засада (+30% шанс крупной добычи, 6 энергии)\n"
        "• <code>отдых [N]</code> — Отдохнуть (съесть N порций мяса, +20 энергии каждая)\n"
        "• <code>/topl</code> — Топ 10 игроков по уровню\n\n"
        "<b>Основное меню:</b>\n"
        "• 📍 Локации — переход между локациями\n"
        "• 🎒 Инвентарь — просмотр и управление предметами\n"
        "• 🛒 Магазин — покупка оружия и снаряжения\n"
        "• 📜 Квесты — список доступных заданий\n"
        "• 👤 Профиль — статистика и навыки\n"
        "• 🎯 Навыки — прокачка характеристик\n"
        "• 🏆 Аукцион — торговля с другими игроками\n"
        "• 🔄 Сменить режим — переключение между свободным и сюжетным режимами\n\n"
        "<b>Энергия:</b>\n"
        "• Максимум: 100 ед.\n"
        "• Восстановление: +1 каждые 5 минут\n"
        "• Отдых: +20 за порцию мяса\n\n"
        "<b>Прогресс:</b>\n"
        "• Откройте следующую локацию при 80% прогресса\n"
        "• Босс доступен при 70% прогресса и выполнении сюжетного квеста"
    )
    await message.answer(help_text, reply_to_message_id=message.message_id)


@router.message(F.text == "/topl")
async def cmd_top_players(message: Message):
    from bot.database.queries import get_all_users
    from bot.database.models import User

    async with async_session() as session:
        users = await get_all_users(session)

        # Sort by level, then by exp
        sorted_users = sorted(users, key=lambda u: (u.level, u.exp), reverse=True)
        top_10 = sorted_users[:10]

        text = "🏆 <b>Топ 10 игроков по уровню</b>\n\n"
        for idx, player in enumerate(top_10, 1):
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"

            username = player.username if player.username else f"ID: {player.telegram_id}"
            exp_needed = player.level * player.level * 100
            text += f"{medal} {idx}. {username} — Уровень {player.level} ({player.exp}/{exp_needed} XP)\n"

        await message.answer(text, reply_to_message_id=message.message_id)


@router.callback_query(F.data.startswith("toggle_mode_"))
@retry(retry_count=3)
async def toggle_mode(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        old_mode = user.game_mode
        new_mode = "story" if user.game_mode == "free" else "free"
        user.game_mode = new_mode

        extra_note = ""
        from bot.game_logic.locations import (
            get_unlocked_locations, get_location_order, can_unlock_location,
            get_location, LOCATIONS
        )

        if new_mode == "story":
            unlocked_story = get_unlocked_locations(user.location_progress, "story")
            order = get_location_order()
            unlocked_ids = [loc.id for loc in unlocked_story]

            best_loc_id = "forest"
            for loc_id in order:
                if loc_id in unlocked_ids:
                    best_loc_id = loc_id

            loc_exists = user.current_location in LOCATIONS
            current_unlocked = user.current_location in unlocked_ids
            if loc_exists:
                can_unlock = can_unlock_location(user.current_location, user.location_progress, "story")
            else:
                can_unlock = False

            if (not loc_exists) or (not current_unlocked) or (not can_unlock):
                old_loc_name = user.current_location
                old_loc_obj = get_location(old_loc_name)
                old_label = f"{old_loc_obj.emoji} {old_loc_obj.name}" if old_loc_obj else old_loc_name
                new_loc_obj = get_location(best_loc_id)
                new_label = f"{new_loc_obj.emoji} {new_loc_obj.name}" if new_loc_obj else best_loc_id
                user.current_location = best_loc_id
                extra_note = f"\n⚠️ Локация {old_label} недоступна в сюжете, переключено на {new_label}"
            else:
                best_loc_id = user.current_location
                extra_note = "\n✅ Текущая локация разрешена в сюжете"
        else:
            if (user.current_location not in LOCATIONS) or (not can_unlock_location(user.current_location, user.location_progress, "free")):
                old_loc = user.current_location
                user.current_location = "forest"
                new_loc_obj = get_location("forest")
                new_label = f"{new_loc_obj.emoji} {new_loc_obj.name}" if new_loc_obj else "Лес"
                extra_note = f"\n⚠️ Локация '{old_loc}' сброшена на {new_label}"

        await session.commit()
        await session.refresh(user)

        mode_text = "Свободный режим" if user.game_mode == "free" else "Сюжетный режим"
        location = get_location(user.current_location)

        await callback.answer(f"✅ Режим изменён на {mode_text}!")

        try:
            await callback.message.edit_text(
                f"🦌 <b>Главное меню</b>\n\n"
                f"🎮 Режим: {mode_text} (было: {'Свободный' if old_mode == 'free' else 'Сюжетный'}){extra_note}\n"
                f"📍 Текущая локация: {location.emoji if location else '📍'} {location.name if location else user.current_location}\n"
                f"⚡ Энергия: {user.energy}/{user.max_energy}\n"
                f"💰 Монеты: {user.coins}\n"
                f"⭐ Звёзды: {user.stars}\n"
                f"📊 Уровень: {user.level}",
                reply_markup=get_main_menu_keyboard(user.telegram_id, user.game_mode)
            )
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise


@router.callback_query(F.data.startswith("auction_"))
@retry(retry_count=3)
async def show_auction(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.edit_text(
            "🏆 <b>Аукцион</b>\n\n"
            "Функционал аукциона в разработке!",
            reply_markup=get_main_menu_keyboard(callback.from_user.id, "free")  # Temporarily
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(F.data.startswith("menu_"))
@retry(retry_count=3)
async def show_menu(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)

        location = get_location(user.current_location)
        mode_text = "Свободный режим" if user.game_mode == "free" else "Сюжетный режим"

        await callback.answer()
        try:
            await callback.message.edit_text(
                f"🦌 <b>Главное меню</b>\n\n"
                f"🎮 Режим: {mode_text}\n"
                f"📍 Текущая локация: {location.emoji} {location.name}\n"
                f"⚡ Энергия: {user.energy}/{user.max_energy}\n"
                f"💰 Монеты: {user.coins}\n"
                f"⭐ Звёзды: {user.stars}\n"
                f"📊 Уровень: {user.level}",
                reply_markup=get_main_menu_keyboard(user.telegram_id, user.game_mode)
            )
        except (TelegramBadRequest, TelegramRetryAfter) as e:
            if "message is not modified" not in str(e):
                raise
