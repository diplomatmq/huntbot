from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard(game_mode: str = "free"):
    buttons = []

    mode_text = "Свободный" if game_mode == "free" else "Сюжетный"

    # Location and inventory buttons are always available
    buttons.append(
        [
            InlineKeyboardButton(text="📍 Локации", callback_data="locations"),
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory")
        ]
    )
    
    # Quests button only in story mode
    if game_mode == "story":
        buttons.append(
            [
                InlineKeyboardButton(text="📜 Квесты", callback_data="quests")
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(text="🛒 Магазин", callback_data="shop"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(text="🎯 Навыки", callback_data="skills"),
            InlineKeyboardButton(text="🏆 Аукцион", callback_data="auction")
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(text=f"🔄 {mode_text} режим", callback_data="toggle_mode")
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
