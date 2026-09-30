from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.internal.enums import ModelMenuBtns, PhotoMenuBtns

FAQ_URL = "https://mod.staisupov.ru/"


class ModelMenuOption(CallbackData, prefix="model_menu"):
    action: ModelMenuBtns


class UploadPhotoOption(CallbackData, prefix="photo_menu"):
    action: PhotoMenuBtns
    chat_id: int


def get_model_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="💰 Стоимость и сроки",
        callback_data=ModelMenuOption(action=ModelMenuBtns.DETAILS),
    )
    kb.button(
        text="📋 Требования к фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.REQUIREMENTS_BEFORE_PAYMENT),
    )
    kb.button(text="📝 Часто задаваемые вопросы", url=FAQ_URL)
    kb.button(text="Перейти к оплате", callback_data="payment")
    kb.adjust(1)
    return kb.as_markup()


def get_requirements_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="💰 Стоимость и сроки",
        callback_data=ModelMenuOption(action=ModelMenuBtns.DETAILS),
    )
    kb.button(text="📝 Часто задаваемые вопросы", url=FAQ_URL)
    kb.button(text="Перейти к оплате", callback_data="payment")
    kb.adjust(1)
    return kb.as_markup()


def get_details_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="📋 Требования к фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.REQUIREMENTS_BEFORE_PAYMENT),
    )
    kb.button(text="📝 Часто задаваемые вопросы", url=FAQ_URL)
    kb.button(text="Перейти к оплате", callback_data="payment")
    kb.adjust(1)
    return kb.as_markup()


def get_photo_buttons(chat_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅",
        callback_data=UploadPhotoOption(action=PhotoMenuBtns.ACCEPT, chat_id=chat_id),
    )
    kb.button(
        text="❌",
        callback_data=UploadPhotoOption(action=PhotoMenuBtns.DECLINE, chat_id=chat_id),
    )
    return kb.as_markup()


def get_rejected_photo_buttons() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="📋 Требования к фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.REQUIREMENTS_AFTER_PAYMENT),
    )
    kb.button(
        text="Оставить прежнее фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.KEEP_PHOTO),
    )
    kb.adjust(1)
    return kb.as_markup()


def get_keep_rejected_photo_buttons() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Оставить прежнее фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.CONFIRM_KEEP_PHOTO),
    )
    kb.button(
        text="📋 Требования к фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.REQUIREMENTS_AFTER_PAYMENT),
    )
    kb.button(
        text="Загрузить новое фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.UPLOAD_NEW_PHOTO),
    )
    kb.adjust(1)
    return kb.as_markup()


def get_photo_requirements_buttons() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Оставить прежнее фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.KEEP_PHOTO),
    )
    kb.button(
        text="Загрузить новое фото",
        callback_data=ModelMenuOption(action=ModelMenuBtns.UPLOAD_NEW_PHOTO),
    )
    kb.adjust(1)
    return kb.as_markup()


def get_accept_button(chat_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅",
        callback_data=UploadPhotoOption(action=PhotoMenuBtns.ACCEPT, chat_id=chat_id),
    )
    return kb.as_markup()
