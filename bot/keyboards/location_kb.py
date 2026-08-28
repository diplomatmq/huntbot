from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.game_logic.locations import LocationData


def get_locations_keyboard(unlocked_locations):
    buttons = []
    
    for location in unlocked_locations:
        buttons.append([
            InlineKeyboardButton(
                text=f"{location.emoji} {location.name}",
                callback_data=f"travel_{location.id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="🏠 Меню", callback_data="menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
