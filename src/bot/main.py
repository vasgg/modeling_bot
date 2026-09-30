import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand

from bot.config import get_settings
from bot.handlers.chat_guard import router as chat_guard_router
from bot.handlers.client_handlers import router as client_router
from bot.handlers.errors_handler import router as errors_router
from bot.handlers.moderator_handlers import router as moderator_router
from bot.internal.helpers import setup_logs
from bot.internal.notify_admin import on_shutdown, on_startup
from bot.middlewares.updates_dumper_middleware import UpdatesDumperMiddleware

logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    default_commands = [
        BotCommand(command="start", description="Главное меню"),
    ]
    await bot.set_my_commands(default_commands)


async def main() -> None:
    setup_logs("modelling_bot")
    settings = get_settings()

    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.REDIS_URL.unicode_string())

    dispatcher = Dispatcher(
        storage=storage, events_isolation=SimpleEventIsolation(), settings=settings
    )
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(set_bot_commands)
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    dispatcher.include_routers(
        chat_guard_router, moderator_router, client_router, errors_router
    )
    logger.info("modelling bot started")
    await dispatcher.start_polling(bot)


def run_main() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
