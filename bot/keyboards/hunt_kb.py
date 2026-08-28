from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_bait_keyboard(user_id: int, baits):
    buttons = []

    for bait in baits:
        display_name = bait["name"].replace("_", " ").capitalize()
        buttons.append([
            InlineKeyboardButton(
                text=f"🍖 {display_name} x{bait['quantity']}",
                callback_data=f"use_bait_{bait['id']}_{user_id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🏠 Назад", callback_data=f"menu_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_hunt_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="🎯 Охотиться", callback_data=f"hunt_{user_id}"),
            InlineKeyboardButton(text="⏩ Пропустить кулдаун (1⭐)", callback_data=f"skip_cooldown_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_guaranteed_hit_keyboard(invoice_url: str, star_cost: int = 1):
    buttons = [
        [
            InlineKeyboardButton(text=f"⭐ Гарантированное попадание ({star_cost}⭐)", url=invoice_url)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skip_cooldown_keyboard(invoice_url: str, star_cost: int = 1):
    buttons = [
        [
            InlineKeyboardButton(text=f"⏩ Пропустить кулдаун ({star_cost}⭐)", url=invoice_url)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
