import logging
from pathlib import Path

from aiogram import html
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, InlineKeyboardMarkup, Message, User

logger = logging.getLogger(__name__)

# file_id is only valid for the bot that uploaded the file, so it is learned at
# runtime: the first send after a restart uploads the file, later ones reuse the id.
_photo_file_ids: dict[str, str] = {}


def display_name(user: User) -> str:
    """HTML-safe full name, plus @username on a new line when present."""
    name = html.quote(user.full_name)
    if user.username:
        name += f"\n@{user.username}"
    return name


def user_header(user: User) -> str:
    """Bold "uid:<id>" + name block; the uid line is parsed by moderator replies."""
    return f"<b>uid:{user.id}\n{display_name(user)}</b>"


def _extract_uid_from_reply(reply: Message) -> int | None:
    source = reply.caption or reply.text or ""
    first_line = source.split("\n", 1)[0].strip()
    if not first_line.startswith("uid:"):
        return None
    try:
        return int(first_line.split(":", 1)[1])
    except (ValueError, IndexError):
        return None


async def moderator_reply_dispatch(message: Message) -> None:
    """Relay moderator's reply to the user whose uid is in the replied message."""
    reply = message.reply_to_message
    if not reply:
        return

    target_chat_id = _extract_uid_from_reply(reply)
    if not target_chat_id:
        return

    await message.copy_to(chat_id=target_chat_id)


async def answer_with_photo(
    message: Message,
    caption: str,
    file_name: str,
    markup: InlineKeyboardMarkup | None = None,
) -> None:
    if file_id := _photo_file_ids.get(file_name):
        try:
            await message.answer_photo(
                photo=file_id, caption=caption, reply_markup=markup
            )
            return
        except TelegramBadRequest:
            logger.warning("Cached file_id for %s rejected, re-uploading", file_name)
            _photo_file_ids.pop(file_name, None)

    sent = await message.answer_photo(
        photo=FSInputFile(Path(__file__).with_name(file_name)),
        caption=caption,
        reply_markup=markup,
    )
    _photo_file_ids[file_name] = sent.photo[-1].file_id
    logger.info("Uploaded %s, cached its file_id", file_name)
