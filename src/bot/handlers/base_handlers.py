import logging

from contextlib import suppress


from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from bot.config import Settings
from bot.global_ctx import get_global_context
from bot.internal.controllers import answer_with_photo, moderator_reply_dispatch
from bot.internal.enums import ModelMenuBtns, PhotoMenuBtns

from bot.internal.lexicon import texts
from bot.keyboards import (
    ModelMenuOption,
    UploadPhotoOption,
    get_accept_button,
    get_details_kb,
    get_model_kb,
    get_photo_buttons,
    get_photo_requirements_buttons,
    get_rejected_photo_buttons,
    get_requirements_kb,
    get_keep_rejected_photo_buttons,
)
from json import dumps

logger = logging.getLogger(__name__)

router = Router()
image_types = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "image/tiff",
}


@router.message(CommandStart())
async def start_message(message: Message) -> None:
    await message.answer(texts["modeling_welcome"], reply_markup=get_model_kb())


@router.callback_query(ModelMenuOption.filter())
async def model_menu_handler(
    callback: CallbackQuery,
    callback_data: ModelMenuOption,
    settings: Settings,
    state: FSMContext,
):
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
            doc_id = data.get("last_document")
            if not doc_id:
                await callback.answer(
                    "Не найдено последнее загруженное фото-файл. Загрузите документ заново.",
                    show_alert=True,
                )
                return
            await callback.message.answer(texts["patient_keep_photo"])
            name = (
                callback.from_user.full_name + "\n@" + callback.from_user.username
                if callback.from_user.username
                else callback.from_user.full_name
            )
            await callback.message.bot.send_document(
                chat_id=settings.MODEL_CHAT_ID,
                document=doc_id,
                caption=f"<b>uid:{callback.from_user.id}\n{name}</b>\n\n{texts['confirm_keep_photo']}",
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


@router.callback_query(UploadPhotoOption.filter())
async def photo_upload_handler(
    callback: CallbackQuery, callback_data: UploadPhotoOption, state: FSMContext
):
    await callback.answer()
    match callback_data.action:
        case PhotoMenuBtns.ACCEPT:
            await callback.message.bot.send_message(
                callback_data.chat_id, texts["photo_uploaded"]
            )
            key = StorageKey(
                bot_id=callback.message.bot.id,
                chat_id=callback_data.chat_id,
                user_id=callback_data.chat_id,
            )
            client_state = FSMContext(storage=state.storage, key=key)
            await client_state.update_data(paid=False)
            await callback.message.reply(texts["admin_accept_photo"])
        case PhotoMenuBtns.DECLINE:
            await callback.message.bot.send_message(
                callback_data.chat_id,
                texts["photo_rejected"],
                reply_markup=get_rejected_photo_buttons(),
            )
            await callback.message.reply(texts["admin_deny_photo"])


@router.callback_query(F.data == "payment")
async def model_payment_handler(callback: CallbackQuery, settings: Settings):
    await callback.answer()
    amount = 3000 * 100
    prices = [LabeledPrice(label="Оплатить", amount=amount)]
    description = "Услуга моделирования."
    provider_data = dumps({
      "receipt": {
        "items": [
          {
            "description": description,
            "quantity": 1,
            "amount": {
              "value": 3000,
              "currency": "RUB"
            },
            "vat_code": 1,
            "payment_mode": "full_payment",
            "payment_subject": "service"
          }
        ]
      }
    })
    await callback.message.answer_invoice(
        title=description,
        description=texts["payment_description"],
        payload="model",
        provider_token=settings.PAYMENT_PROVIDER_TOKEN.get_secret_value(),
        currency="RUB",
        prices=prices,
        provider_data=provider_data,
        need_email = True,
        send_email_to_provider = True,
    )


@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(
    message: Message, state: FSMContext, settings: Settings
):
    await state.update_data(paid=True)
    await answer_with_photo(
        message=message,
        caption=texts["payment_success"],
        file_name="example_sending.jpg",
    )
    name = (
        message.from_user.full_name + "\n@" + message.from_user.username
        if message.from_user.username
        else message.from_user.full_name
    )
    await message.bot.send_message(
        settings.MODEL_CHAT_ID, texts["new_payment"].format(message.from_user.id, name)
    )


@router.message(F.photo)
async def on_photo(message: Message, state: FSMContext, settings: Settings):
    if message.from_user.id == settings.MODERATOR:
        await moderator_reply_dispatch(message, settings)
        return

    data = await state.get_data()
    if not data.get("paid", False):
        await message.answer(texts["not_paid_or_work_in_progress"])
        return
    await answer_with_photo(
        message=message,
        caption=texts["photo_low_quality"],
        file_name="example_sending.jpg",
    )


@router.message(F.document)
async def on_document(message: Message, state: FSMContext, settings: Settings):
    if message.from_user.id == settings.MODERATOR:
        await moderator_reply_dispatch(message, settings)
        return

    doc = message.document
    if not doc or (doc.mime_type not in image_types):
        return

    data = await state.get_data()
    if not data.get("paid", False):
        await message.answer(texts["not_paid_or_work_in_progress"])
        return

    user_caption = message.caption or ""
    name = (
        message.from_user.full_name + "\n@" + message.from_user.username
        if message.from_user.username
        else message.from_user.full_name
    )
    await message.bot.send_document(
        chat_id=settings.MODEL_CHAT_ID,
        document=doc.file_id,
        caption=f"<b>uid:{message.from_user.id}\n{name}</b>\n\n{user_caption}",
        reply_markup=get_photo_buttons(chat_id=message.from_user.id),
    )
    await state.update_data(last_document=doc.file_id)
    await message.answer(texts["photo_sent"])


@router.message(F.text)
async def text_reply(message: Message, settings: Settings):
    if message.from_user.id != settings.MODERATOR:
        await message.answer(texts["no_photo_message"])
        return
    await moderator_reply_dispatch(message, settings)


@router.message(
    lambda message, settings: message.chat.id == settings.MODEL_CHAT_ID,
    lambda message, settings: message.from_user.id == settings.MODERATOR,
    lambda message: bool(message.reply_to_message),
)
async def moderator_reply_handler(message: Message, state: FSMContext) -> None:
    """Forward moderator replies from log chat to the original user."""
    logger.info(
        "Processing moderator reply %s to %s",
        message.message_id,
        message.reply_to_message.message_id,
    )

    global_ctx = get_global_context(message.bot, state.storage)
    data = await global_ctx.get_data()
    log_user_message_map: dict[str, int] = data.get("log_user_message_map", {})

    user_id = log_user_message_map.get(str(message.reply_to_message.message_id))
    if user_id is None:
        logger.warning(
            "No user_id found for log message %s", message.reply_to_message.message_id
        )
        return

    if message.text:
        await message.bot.send_message(chat_id=user_id, text=message.text)
