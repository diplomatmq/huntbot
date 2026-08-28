from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_quests_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="quests"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
