import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware to log all user interactions"""
    
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        username = event.from_user.username
        
        if isinstance(event, Message):
            logger.info(f"[{datetime.now()}] User {username} ({user_id}): {event.text}")
        elif isinstance(event, CallbackQuery):
            logger.info(f"[{datetime.now()}] User {username} ({user_id}): Callback {event.data}")
        
        return await handler(event, data)
