import asyncio
import logging
from functools import wraps
from aiogram.exceptions import TelegramRetryAfter

logger = logging.getLogger(__name__)


def retry(retry_count: int = 3):
    """Decorator to retry a function on TelegramRetryAfter errors"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retry_count:
                try:
                    return await func(*args, **kwargs)
                except TelegramRetryAfter as e:
                    attempt += 1
                    retry_after = e.retry_after
                    logger.warning(
                        f"TelegramRetryAfter hit (attempt {attempt}/{retry_count}). "
                        f"Retrying after {retry_after} seconds."
                    )
                    await asyncio.sleep(retry_after)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
