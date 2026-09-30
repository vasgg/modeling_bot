import logging
import traceback

from aiogram import Bot, Router, html
from aiogram.types import ErrorEvent

from bot.config import Settings

logger = logging.getLogger(__name__)

router = Router()


@router.errors()
async def error_handler(error_event: ErrorEvent, bot: Bot, settings: Settings) -> None:
    exc = error_event.exception
    logger.exception("Exception while handling update", exc_info=exc)

    exc_traceback = "".join(traceback.format_exception(exc))
    tb = html.quote(exc_traceback[-3000:])
    exc_name = html.quote(type(exc).__name__)
    exc_text = html.quote(str(exc)[:500])

    error_message = (
        f"🚨 <b>An error occurred</b> 🚨\n\n"
        f"<b>Type:</b> {exc_name}\n<b>Message:</b> {exc_text}\n\n"
        f"<b>Traceback:</b>\n<code>{tb}</code>"
    )
    await bot.send_message(settings.ADMIN, error_message, disable_notification=True)
