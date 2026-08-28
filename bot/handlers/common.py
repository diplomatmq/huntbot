from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from bot.keyboards.main_kb import get_main_menu_keyboard
from bot.database.db import async_session
from bot.database.queries import get_or_create_user
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


@router.message(lambda msg: msg.text and msg.text.split()[0].lower() in ["/menu", "меню"])
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
        "• <code>хант</code> или <code>выстрел</code> — Охотиться (5 энергии)\n"
        "• <code>след</code> — Найти следы (+20% шанс редкого животного, 3 энергии)\n"
        "• <code>приманка</code> — Выбрать и установить приманку (4 энергии)\n"
        "• <code>засада</code> — Засада (+30% шанс крупной добычи, 6 энергии)\n"
        "• <code>отдых [N]</code> — Отдохнуть (съесть N порций мяса, +20 энергии каждая)\n\n"
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


@router.callback_query(F.data.startswith("toggle_mode_"))
@retry(retry_count=3)
async def toggle_mode(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user.game_mode = "story" if user.game_mode == "free" else "free"
        await session.commit()
        await session.refresh(user)

        mode_text = "Свободный режим" if user.game_mode == "free" else "Сюжетный режим"
        location = get_location(user.current_location)

        await callback.answer(f"✅ Режим изменён на {mode_text}!")

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
