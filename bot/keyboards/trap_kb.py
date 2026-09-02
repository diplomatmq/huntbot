from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_trap_payment_keyboard(invoice_link: str, star_cost: int):
    """Keyboard with payment link for trap cooldown skip"""
    buttons = [
        [InlineKeyboardButton(text=f"💳 Оплатить {star_cost} ⭐", url=invoice_link)],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_trap_payment")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
