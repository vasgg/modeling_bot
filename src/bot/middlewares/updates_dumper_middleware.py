import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class UpdatesDumperMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(event.model_dump_json(exclude_unset=True))
        res = await handler(event, data)
        if res is UNHANDLED:
            logger.warning("UNHANDLED")
        return res
