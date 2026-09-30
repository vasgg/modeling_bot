import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated

from bot.config import Settings

logger = logging.getLogger(__name__)

router = Router()


@router.my_chat_member(
    ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION),
    F.chat.type != ChatType.PRIVATE,
)
async def leave_foreign_chat(
    event: ChatMemberUpdated, bot: Bot, settings: Settings
) -> None:
    """The bot works 1-on-1 with clients; the model chat is the only allowed group."""
    if event.chat.id == settings.MODEL_CHAT_ID:
        return
    logger.warning(
        "Added to foreign chat %s (%r) by %s, leaving",
        event.chat.id,
        event.chat.title,
        event.from_user.id,
    )
    await bot.leave_chat(event.chat.id)
