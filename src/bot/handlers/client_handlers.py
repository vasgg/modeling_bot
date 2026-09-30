import json
import logging
from contextlib import suppress

from aiogram import F, Router, html
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from bot.config import Settings
from bot.internal.controllers import answer_with_photo, display_name, user_header
from bot.internal.enums import ModelMenuBtns
from bot.internal.lexicon import texts
from bot.keyboards import (
    ModelMenuOption,
    get_accept_button,
    get_details_kb,
    get_keep_rejected_photo_buttons,
    get_model_kb,
    get_photo_buttons,
    get_photo_requirements_buttons,
    get_requirements_kb,
)

logger = logging.getLogger(__name__)

# The bot talks to clients only in private chats.
router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)

PRICE_RUB = 3000
ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
        "image/tiff",
        "video/mp4",
        "video/quicktime",
        "application/pdf",
    }
)


@router.message(CommandStart())
async def start_message(message: Message) -> None:
    await message.answer(texts["modeling_welcome"], reply_markup=get_model_kb())


@router.callback_query(ModelMenuOption.filter())
async def model_menu_handler(
    callback: CallbackQuery,
    callback_data: ModelMenuOption,
    settings: Settings,
    state: FSMContext,
) -> None:
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete_reply_markup()
    data = await state.get_data()
    match callback_data.action:
        case ModelMenuBtns.UPLOAD_NEW_PHOTO:
            if not data.get("paid", False):
                return
            await answer_with_photo(
                message=callback.message,
                caption=texts["payment_success"],
                file_name="example_sending.jpg",
            )
        case ModelMenuBtns.KEEP_PHOTO:
            if not data.get("paid", False):
                return
            await callback.message.answer(
                text=texts["keep_photo"], reply_markup=get_keep_rejected_photo_buttons()
            )
        case ModelMenuBtns.CONFIRM_KEEP_PHOTO:
            if not data.get("paid", False):
                return
            doc_id = data.get("last_document")
            if not doc_id:
                await callback.message.answer(texts["last_document_not_found"])
                return
            await callback.message.answer(texts["patient_keep_photo"])
            await callback.bot.send_document(
                chat_id=settings.MODEL_CHAT_ID,
                document=doc_id,
                caption=f"{user_header(callback.from_user)}\n\n"
                f"{texts['confirm_keep_photo']}",
                reply_markup=get_accept_button(chat_id=callback.from_user.id),
            )
        case ModelMenuBtns.REQUIREMENTS_BEFORE_PAYMENT:
            await answer_with_photo(
                message=callback.message,
                caption=texts["photo_requirements"],
                file_name="example_photo.jpg",
                markup=get_requirements_kb(),
            )
        case ModelMenuBtns.REQUIREMENTS_AFTER_PAYMENT:
            await answer_with_photo(
                message=callback.message,
                caption=texts["photo_requirements"],
                file_name="example_photo.jpg",
                markup=get_photo_requirements_buttons(),
            )
        case ModelMenuBtns.DETAILS:
            await callback.message.answer(
                texts["modeling_message"], reply_markup=get_details_kb()
            )


@router.callback_query(F.data == "payment")
async def model_payment_handler(callback: CallbackQuery, settings: Settings) -> None:
    await callback.answer()
    description = "Услуга моделирования."
    provider_data = json.dumps(
        {
            "receipt": {
                "items": [
                    {
                        "description": description,
                        "quantity": 1,
                        "amount": {"value": PRICE_RUB, "currency": "RUB"},
                        "vat_code": 1,
                        "payment_mode": "full_payment",
                        "payment_subject": "service",
                    }
                ]
            }
        }
    )
    await callback.message.answer_invoice(
        title=description,
        description=texts["payment_description"],
        payload="model",
        provider_token=settings.PAYMENT_PROVIDER_TOKEN.get_secret_value(),
        currency="RUB",
        prices=[LabeledPrice(label="Оплатить", amount=PRICE_RUB * 100)],
        provider_data=provider_data,
        need_email=True,
        send_email_to_provider=True,
    )


@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(
    message: Message, state: FSMContext, settings: Settings
) -> None:
    await state.update_data(paid=True)
    await answer_with_photo(
        message=message,
        caption=texts["payment_success"],
        file_name="example_sending.jpg",
    )
    user = message.from_user
    await message.bot.send_message(
        settings.MODEL_CHAT_ID, texts["new_payment"].format(user.id, display_name(user))
    )


@router.message(F.photo)
async def on_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("paid", False):
        await message.answer(texts["not_paid_or_work_in_progress"])
        return
    await answer_with_photo(
        message=message,
        caption=texts["photo_low_quality"],
        file_name="example_sending.jpg",
    )


@router.message(F.video)
async def on_video(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("paid", False):
        await message.answer(texts["not_paid_or_work_in_progress"])


@router.message(F.document)
async def on_document(message: Message, state: FSMContext, settings: Settings) -> None:
    data = await state.get_data()
    if not data.get("paid", False):
        await message.answer(texts["not_paid_or_work_in_progress"])
        return

    doc = message.document
    if doc.mime_type not in ALLOWED_MIME_TYPES:
        await message.answer(texts["unsupported_file"])
        return

    await message.bot.send_document(
        chat_id=settings.MODEL_CHAT_ID,
        document=doc.file_id,
        caption=f"{user_header(message.from_user)}\n\n"
        f"{html.quote(message.caption or '')}",
        reply_markup=get_photo_buttons(chat_id=message.from_user.id),
    )
    await state.update_data(last_document=doc.file_id)
    await message.answer(texts["photo_sent"])


@router.message(F.audio | F.voice | F.video_note)
async def on_unsupported_file(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("paid", False):
        await message.answer(texts["not_paid_or_work_in_progress"])
        return
    await message.answer(texts["unsupported_file"])


@router.message(F.text)
async def text_reply(message: Message, settings: Settings, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("paid", False):
        await message.answer(texts["no_photo_message"])
        return
    await message.bot.send_message(
        settings.MODEL_CHAT_ID,
        text=f"{user_header(message.from_user)}\n\n{html.quote(message.text)}",
    )
