from aiogram.types import CallbackQuery, Message

from bot.config import Settings


def in_model_chat(event: Message | CallbackQuery, settings: Settings) -> bool:
    if isinstance(event, CallbackQuery):
        chat = event.message.chat if event.message else None
    else:
        chat = event.chat
    return chat is not None and chat.id == settings.MODEL_CHAT_ID


def from_moderator(event: Message | CallbackQuery, settings: Settings) -> bool:
    return event.from_user is not None and event.from_user.id == settings.MODERATOR
