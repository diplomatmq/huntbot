from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_inventory_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="💰 Продать предметы", callback_data=f"sell_items_{user_id}"),
            InlineKeyboardButton(text="🔧 Экипировать", callback_data=f"equip_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🧪 Использовать зелья", callback_data=f"use_potions_{user_id}"),
            InlineKeyboardButton(text="🪤 Улучшить ловушку", callback_data=f"upgrade_trap_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
