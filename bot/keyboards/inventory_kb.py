from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_inventory_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="💰 Продать предметы", callback_data="sell_items"),
            InlineKeyboardButton(text="🔧 Экипировать", callback_data="equip")
        ],
        [
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
