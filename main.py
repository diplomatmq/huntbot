import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.config import BOT_TOKEN
from bot.dispatcher import get_dispatcher
from bot.database.db import init_db, async_session
from bot.database.queries import migrate_animal_species
from bot.tasks.trap_checker import trap_checker_loop

# Configure logging to suppress unhandled update logs
logging.basicConfig(level=logging.INFO)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Initialize database
    await init_db()

    # Run migration for AnimalSpecies table (one-time)
    async with async_session() as session:
        migration_performed = await migrate_animal_species(session)
        if migration_performed:
            logging.info("AnimalSpecies migration completed successfully.")

    # Get dispatcher with all routers
    dp = await get_dispatcher()

    # Setup scheduler for energy recovery
    scheduler = AsyncIOScheduler()
    scheduler.start()

    # Start trap checker background task
    trap_task = asyncio.create_task(trap_checker_loop(bot))
    logging.info("Started trap checker background task")

    await bot.delete_webhook(drop_pending_updates=True)

    # Only receive messages and callback queries, ignore other updates
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "pre_checkout_query", "successful_payment"]
        )
    finally:
        # Cancel trap checker when bot stops
        trap_task.cancel()
        try:
            await trap_task
        except asyncio.CancelledError:
            logging.info("Trap checker task cancelled")


if __name__ == "__main__":
    asyncio.run(main())
