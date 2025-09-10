import asyncio
import logging
import logging.config

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand

from bot.handlers.base_handlers import router as base_router
from bot.handlers.errors_handler import router as errors_router
from bot.internal.notify_admin import on_shutdown, on_startup

from bot.internal.helpers import setup_logs
from bot.middlewares.updates_dumper_middleware import UpdatesDumperMiddleware

from bot.global_ctx import init_global
from bot.config import get_settings


async def set_bot_commands(bot: Bot) -> None:
    default_commands = [
        BotCommand(command="/start", description="Главное меню"),
    ]
    await bot.set_my_commands(default_commands)


async def main():
    setup_logs("modelling_bot")
    settings = get_settings()

    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.REDIS_URL.unicode_string())

    await init_global(storage, bot)

    dispatcher = Dispatcher(
        storage=storage, events_isolation=SimpleEventIsolation(), settings=settings
    )
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(set_bot_commands)
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    dispatcher.include_routers(base_router, errors_router)
    logging.info("modelling bot started")
    await dispatcher.start_polling(bot)


def run_main():
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
