"""Admin message router connect"""
import time
from asyncio import gather

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from shared.models.category import ContentItem
from shared.utils.callbacks import (SendMailing, Start, ChangePrice,
                                    Cabinet, PromoCreate, DiscountsCallback, \
    DiscountsFinish, SubscriptionSettings)
from shared.utils.config import settings
from shared.utils.functions_admin import keyboard_back

from shared.utils.db import MongoDbClient
from shared.utils.fsm_state import (CategoryName, CategoryMedia, MailingAll,
                                    ChangePriceState, DiscountCreateState)
from shared.utils.functions import generate_unique_category_id, send_category_content

router = Router()


@router.message(CategoryName.category_name)
async def _(message: Message,
            bot: Bot,
            db: MongoDbClient,
            state: FSMContext,
            locale: TranslatorRunner):
    if message.text:
        data = await state.get_data()
        message_id = data.get("message_id")
        parent_id = data.get("parent_id")
        category_id = await generate_unique_category_id()
        keyboard = await keyboard_back(parent_id, locale)
        await db.category.insert_one({
            "id": category_id,
            "parent_id": parent_id if parent_id else None,
            "name": message.text,
            "created_at": time.time()})
        await bot.delete_message(chat_id=message.from_user.id,
                                 message_id=message.message_id)
        await bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=int(message_id),
            text=locale.category.created(name=message.text),
            reply_markup=keyboard)
    await state.clear()


@router.message(CategoryName.category_rename)
async def _(message: Message,
            bot: Bot,
            db: MongoDbClient,
            state: FSMContext,
            locale: TranslatorRunner):
    data = await state.get_data()
    message_id = data.get("message_id")
    parent_id = data.get("parent_id")
    current_id = data.get("current_id")
    await db.category.update_one({"id": current_id},
                                 {"name": message.text})
    keyboard = await keyboard_back(parent_id, locale)
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=int(message_id),
                                text=locale.category.renamed(),
                                reply_markup=keyboard)
    await state.clear()


@router.message(CategoryMedia.category_media)
async def _(message: Message,
            state: FSMContext,
            db: MongoDbClient,
            locale: TranslatorRunner,
            bot: Bot,
            album: list = None): # pylint: disable=all
    # I off pylint because I want to have the 6 arguments in this func
    # Because its faster
    data = await state.get_data()
    current_id = data.get("current_id")
    try:
        await bot.delete_message(chat_id=message.from_user.id,
                                 message_id=int(data.get("message_id")))
        if album:
            await gather(*[
                bot.delete_message(
                    chat_id=message.from_user.id,
                    message_id=msg.message_id
                ) for msg in album
            ], return_exceptions=True)
        else:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=message.message_id
            )
    except TelegramBadRequest as e:
        print(f"Ошибка при удалении сообщений: {e}")
    if message.text:
        await db.category.update_one(
            {"id": current_id},
            {"caption": message.html_text},
            upsert=True)
        try:
            await bot.delete_message(chat_id=message.from_user.id,
                                     message_id=int(data.get("message_id")))
        except TelegramBadRequest:
            pass
        # pylint: disable=duplicate-code
        await send_category_content(
            bot=bot,
            message=message,
            current_id=current_id,
            locale=locale,
        )
        await state.clear()

    if album:
        media_group_ids = []
        for msg in album:
            if msg.photo:
                media_group_ids.append(msg.photo[-1].file_id)
                file_type = "photos"
            elif msg.document:
                media_group_ids.append(msg.document.file_id)
                file_type = "documents"
            elif msg.video:
                media_group_ids.append(msg.video.file_id)
                file_type = "videos"
            elif msg.audio:
                media_group_ids.append(msg.audio.file_id)
                file_type = "audios"

        content_data = [ContentItem(type="media_group", file_id=media_group_ids).model_dump()]

    else:
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photos"
        elif message.document:
            file_id = message.document.file_id
            file_type = "documents"
            category = await db.category.find_one({"id": current_id})
            if category.documents:

                existing_files = category.documents[0].file_id
                if isinstance(existing_files, str):
                    content_data = [{"type": "media_group", "file_id": [existing_files, file_id]}]
                else:
                    content_data = [{"type": "media_group", "file_id": [*existing_files, file_id]}]
                await db.category.update_one(
                    {"id": current_id},
                    {"documents": content_data}
                )
                # pylint: disable=duplicate-code
                await send_category_content(
                    bot=bot,
                    message=message,
                    current_id=current_id,
                    locale=locale,
                )
                await state.clear()
                return


        elif message.video:
            file_id = message.video.file_id
            file_type = "videos"
        elif message.audio:
            file_id = message.audio.file_id
            file_type = "audios"
        elif message.voice:
            file_id = message.voice.file_id
            file_type = "voices"
        elif message.video_note:
            file_id = message.video_note.file_id
            file_type = "video_notes"
        else:
            return

        content_data = [ContentItem(type="solo", file_id=[file_id]).model_dump()]

    await db.category.update_one(
        {"id": current_id},
        {file_type: content_data},
        upsert=True
    )
    # pylint: disable=duplicate-code
    await send_category_content(
        bot=bot,
        message=message,
        current_id=current_id,
        locale=locale,
    )
    await state.clear()


@router.message(MailingAll.mailing_send)
async def confirm_mailing(message: Message,
                          state: FSMContext,
                          locale: TranslatorRunner,
                          bot: Bot):
    """
    Mailing send
    :param message:
    :param state:
    :param locale:
    :param bot:
    :return:
    """
    data = await state.get_data()
    builder_accept = InlineKeyboardBuilder()
    builder_accept.row(InlineKeyboardButton(
        text=locale.confirm(),
        callback_data=SendMailing(
            mes_id=message.message_id).pack()))
    builder_accept.row(InlineKeyboardButton(
        text=locale.cancel(),
        callback_data=Start().pack()))
    await bot.edit_message_caption(
        chat_id=message.from_user.id,
        message_id=int(data.get('message_id')),
        caption=locale.mailing.check(text=message.html_text),
        reply_markup=builder_accept.as_markup())

    await state.clear()


@router.message(ChangePriceState.change_price)
async def _(message: Message,
            state: FSMContext,
            db: MongoDbClient,
            bot: Bot):
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=message.message_id)
    data = await state.get_data()
    message_id = data.get('message_id')
    period = data.get('period')
    try:
        float_number = float(message.text)
        print(f"float_number: {float_number}")
        await db.config_admin.update_one({"id": 1},
                                         {period: float_number})
        config = await db.config_admin.find_one({"id": 1})
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(
                text="Месяц",
                callback_data=ChangePrice(period="one_month").pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="3 месяца",
                callback_data=ChangePrice(period="three_month").pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="Пол года",
                callback_data=ChangePrice(period="half_year").pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="Год",
                callback_data=ChangePrice(period="year").pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="Промокоды",
                callback_data=PromoCreate().pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="Скидки",
                callback_data=DiscountsCallback().pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="Назад",
                callback_data=Cabinet().pack()))
        await bot.edit_message_caption(
            chat_id=message.from_user.id,
            message_id=message_id,
            caption=f"<b>Актуальные цены:</b>\n"
                    f"<b>1 месяц: </b>{int(config.one_month)}\n"
                    f"<b>3 месяца: </b>{int(config.three_month)}\n"
                    f"<b>6 месяцев: </b>{int(config.half_year)}\n"
                    f"<b>12 месяцев: </b>{int(config.year)}\n\n"
                    f"За какой период нужно изменить цены?",
            reply_markup=keyboard.as_markup()
        )

    except ValueError:
        await bot.send_message(chat_id=message.from_user.id,
                               text="Проверьте правильность введенных данных")
    await state.clear()


@router.message(DiscountCreateState.discount_name)
async def _(message: Message,
            state: FSMContext,
            bot: Bot):
    discount = message.text.lower()
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=message.message_id)
    data = await state.get_data()
    message_id = data.get('message_id')
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="Продолжить",
            callback_data=DiscountsFinish(
                discount=discount).pack()))
    keyboard.row(
        InlineKeyboardButton(
            text="Изменить",
            callback_data=DiscountsCallback().pack()))
    await bot.edit_message_caption(
        chat_id=message.from_user.id,
        message_id=message_id,
        caption=f"Промокод для скидки: {discount} ?",
        reply_markup=keyboard.as_markup()
    )
    await state.clear()


@router.message(DiscountCreateState.discount_price)
async def _(message: Message,
            state: FSMContext,
            db: MongoDbClient,
            bot: Bot):
    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
    data = await state.get_data()
    message_id = data.get('message_id')
    discount = data.get('discount')
    try:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(
                text="Назад",
                callback_data=SubscriptionSettings().pack()))
        price = float(message.text)
        await db.discounts.update_one({"promo_code": discount},
                                      {"price": price,
                                       "created_at": time.time()})
        await bot.edit_message_caption(
            chat_id=message.from_user.id,
            message_id=message_id,
            caption=f"Промокод <code>{discount}</code> зарегестрирован!",
            reply_markup=keyboard.as_markup()
        )
    except ValueError:
        await message.answer(text="Проверьте формат введенных данных"
                                  " (цена должна быть целым числом как 10 100 1000)")
    await state.clear()


@router.message(Command("delete"))
async def _(message: Message,
            bot: Bot,
            locale: TranslatorRunner,
            db: MongoDbClient):
    if message.from_user.id in settings.ADMIN_IDS:
        command_parts = message.text.split()

        if len(command_parts) < 2:
            await message.answer("Пожалуйста, укажите user_id после команды /delete")
            return

        try:
            user_id = int(command_parts[1])
            try:
                await db.users.update_one({"id": user_id},
                                          {"subscribed": False,
                                           "subscribed_date": None,
                                           "subscribed_period": None})
            except:
                pass
            await message.answer(f"Подписка деактивирована для пользователя с ID: {user_id}")

        except ValueError:
            await message.answer("Некорректный user_id. Укажите числовой идентификатор.")
