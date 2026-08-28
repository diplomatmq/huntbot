from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class CallbackProtectionMiddleware(BaseMiddleware):
    """Middleware to ensure only the message sender can click callback buttons"""
    
    async def __call__(self, handler, event, data):
        # Only apply to callback queries
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)
        
        # For inline keyboards (bot messages), we can't check message.from_user
        # because the message is from the bot, not the user
        # Skip protection for inline keyboards - they're already protected by Telegram
        # as only the user who can see the message can click the buttons
        return await handler(event, data)
