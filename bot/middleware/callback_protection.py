from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery


class CallbackProtectionMiddleware(BaseMiddleware):
    """Middleware to ensure only the intended user can click callback buttons"""
    
    async def __call__(self, handler, event, data):
        # Only apply to callback queries
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)
        
        # Extract user_id from callback data if present
        # Format: "action_userId" or "action_param_userId"
        callback_data = event.data
        if callback_data:
            parts = callback_data.split('_')
            # Last part should be user_id
            if len(parts) >= 2 and parts[-1].isdigit():
                user_id_from_callback = int(parts[-1])
                # Check if the user clicking matches the user_id in callback
                if event.from_user.id != user_id_from_callback:
                    await event.answer("❌ Эта кнопка не для вас!", show_alert=True)
                    return
        
        return await handler(event, data)
