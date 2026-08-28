from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest


async def safe_edit_message(message: Message, text: str, **kwargs):
    """
    Safely edit a message, ignoring 'message is not modified' errors.
    
    Args:
        message: The message to edit
        text: New text content
        **kwargs: Additional arguments to pass to edit_text (e.g., reply_markup)
    """
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
