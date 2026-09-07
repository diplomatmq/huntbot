from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_trap_payment_keyboard(invoice_link: str, star_cost: int, user_id: int):
    """Keyboard with payment link for trap payments"""
    buttons = [
        [InlineKeyboardButton(text=f"💳 Оплатить {star_cost} ⭐", url=invoice_link)],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data=f"shop_{user_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_trap_status_keyboard(user_id: int):
    """Keyboard for trap status with skip button"""
    buttons = [
        [InlineKeyboardButton(
            text="⏭️ Пропустить кд (5 ⭐)",
            callback_data=f"skip_trap_trigger_{user_id}"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
