from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_keyboard(user_id: int):
    buttons = [
        [
            InlineKeyboardButton(text="🎯 Навыки", callback_data=f"skills_{user_id}"),
            InlineKeyboardButton(text="🦌 Животные", callback_data=f"animals_{user_id}")
        ],
        [
            InlineKeyboardButton(text="📍 Локации", callback_data=f"locations_{user_id}"),
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data=f"inventory_{user_id}")
        ],
        [
            InlineKeyboardButton(text="📜 Квесты", callback_data=f"quests_{user_id}"),
            InlineKeyboardButton(text="🏠 Меню", callback_data=f"menu_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skills_keyboard(user_id: int, has_points: bool = True):
    buttons = [
        [
            InlineKeyboardButton(text="🎯 +Меткость", callback_data=f"skill_accuracy_{user_id}"),
            InlineKeyboardButton(text="👻 +Скрытность", callback_data=f"skill_stealth_{user_id}")
        ],
        [
            InlineKeyboardButton(text="💪 +Выносливость", callback_data=f"skill_endurance_{user_id}")
        ]
    ]
    
    if not has_points:
        buttons = []  # Disable buttons if no points
    
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"profile_{user_id}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
