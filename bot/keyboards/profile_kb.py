from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="🎯 Навыки", callback_data="skills"),
            InlineKeyboardButton(text="📍 Локации", callback_data="locations")
        ],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="inventory"),
            InlineKeyboardButton(text="📜 Квесты", callback_data="quests")
        ],
        [
            InlineKeyboardButton(text="🏠 Меню", callback_data="menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skills_keyboard(has_points: bool = True):
    buttons = [
        [
            InlineKeyboardButton(text="🎯 +Меткость", callback_data="skill_accuracy"),
            InlineKeyboardButton(text="👻 +Скрытность", callback_data="skill_stealth")
        ],
        [
            InlineKeyboardButton(text="💪 +Выносливость", callback_data="skill_endurance")
        ]
    ]
    
    if not has_points:
        buttons = []  # Disable buttons if no points
    
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="profile")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
