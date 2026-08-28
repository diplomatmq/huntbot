from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard(user_id: int, game_mode: str = "free"):
    buttons = []

    mode_text = "Свободный" if game_mode == "free" else "Сюжетный"

    # Location and inventory buttons are always available
    buttons.append(
        [
            InlineKeyboardButton(text="📍 Локации", callback_data=f"locations_{user_id}"),
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data=f"inventory_{user_id}")
        ]
    )
    
    # Quests button only in story mode
    if game_mode == "story":
        buttons.append(
            [
                InlineKeyboardButton(text="📜 Квесты", callback_data=f"quests_{user_id}")
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(text="🛒 Магазин", callback_data=f"shop_{user_id}"),
            InlineKeyboardButton(text="👤 Профиль", callback_data=f"profile_{user_id}")
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(text="🎯 Навыки", callback_data=f"skills_{user_id}"),
            InlineKeyboardButton(text="🏆 Аукцион", callback_data=f"auction_{user_id}")
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(text=f"🔄 {mode_text} режим", callback_data=f"toggle_mode_{user_id}")
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
