from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class CallbackProtectionMiddleware(BaseMiddleware):
    """Middleware to ensure only the message sender can click callback buttons"""
    
    async def __call__(self, handler, event, data):
        # Only apply to callback queries
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)
        
        # Check if the callback has a message
        if not event.message:
            return await handler(event, data)
        
        # Verify the callback is from the same user who sent the message
        if event.from_user.id != event.message.from_user.id:
            await event.answer("❌ Эта кнопка не для вас!", show_alert=True)
            return
        
        return await handler(event, data)
