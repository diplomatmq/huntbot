from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_quests_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"quests_{user_id}"),
            InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
