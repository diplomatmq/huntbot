import asyncio
import logging
from aiogram import Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from bot.middleware.energy import EnergyMiddleware
from bot.handlers import common, hunt, shop, inventory, location, quest, profile, admin


logger = logging.getLogger(__name__)


async def get_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    
    # Add middlewares
    dp.message.middleware(EnergyMiddleware())
    dp.callback_query.middleware(EnergyMiddleware())
    
    # Error handler for TelegramRetryAfter
    @dp.errors()
    async def retry_after_error_handler(event, **kwargs):
        exception = kwargs.get('exception')
        
        # Try to get exception from event if not in kwargs
        if exception is None and hasattr(event, 'exception'):
            exception = event.exception
        
        # Log with details
        if exception is None:
            logger.error(f"Unhandled error: exception is None. Event type: {type(event).__name__}, kwargs: {list(kwargs.keys())}")
            return False
        
        if isinstance(exception, TelegramRetryAfter):
            retry_after = exception.retry_after
            logger.warning(f"Hit flood limit, retrying after {retry_after} seconds...")
            await asyncio.sleep(retry_after)
            return True
        
        # Log other errors with full traceback
        logger.error(f"Unhandled error: {type(exception).__name__}: {exception}", exc_info=exception)
        return False
    
    dp.include_router(common.router)
    dp.include_router(hunt.router)
    dp.include_router(shop.router)
    dp.include_router(inventory.router)
    dp.include_router(location.router)
    dp.include_router(quest.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    
    return dp
