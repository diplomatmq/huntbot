from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.database.db import async_session
from bot.database.queries import get_or_create_user, update_energy


class EnergyMiddleware(BaseMiddleware):
    """Middleware to automatically update user energy on each interaction"""
    
    async def __call__(self, handler, event, data):
        # Update energy for both messages and callbacks
        user_id = event.from_user.id
        username = event.from_user.username
        
        async with async_session() as session:
            user = await get_or_create_user(session, user_id, username)
            user = await update_energy(session, user)
            data["user"] = user
        
        return await handler(event, data)
