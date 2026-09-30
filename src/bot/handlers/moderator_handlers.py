from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message

from bot.filters import from_moderator, in_model_chat
from bot.internal.controllers import moderator_reply_dispatch
from bot.internal.enums import PhotoMenuBtns
from bot.internal.lexicon import texts
from bot.keyboards import UploadPhotoOption, get_rejected_photo_buttons

# Everything here happens only in the model chat (the doctor's working group).
router = Router()
router.message.filter(in_model_chat)
router.callback_query.filter(in_model_chat)


@router.message(from_moderator, F.photo | F.video | F.document | F.text)
async def moderator_reply(message: Message) -> None:
    await moderator_reply_dispatch(message)


@router.callback_query(UploadPhotoOption.filter())
async def photo_upload_handler(
    callback: CallbackQuery, callback_data: UploadPhotoOption, state: FSMContext
) -> None:
    await callback.answer()
    match callback_data.action:
        case PhotoMenuBtns.ACCEPT:
            await callback.bot.send_message(
                callback_data.chat_id, texts["photo_uploaded"]
            )
            key = StorageKey(
                bot_id=callback.bot.id,
                chat_id=callback_data.chat_id,
                user_id=callback_data.chat_id,
            )
            client_state = FSMContext(storage=state.storage, key=key)
            await client_state.update_data(paid=False)
            await callback.message.reply(texts["admin_accept_photo"])
        case PhotoMenuBtns.DECLINE:
            await callback.bot.send_message(
                callback_data.chat_id,
                texts["photo_rejected"],
                reply_markup=get_rejected_photo_buttons(),
            )
            await callback.message.reply(texts["admin_deny_photo"])
