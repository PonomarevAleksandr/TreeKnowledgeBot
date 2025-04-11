"""
Functions
"""
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Union
from dateutil.relativedelta import relativedelta
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, \
                           InputMediaVideo, InputMediaDocument, InputMediaAudio,
                           InputMediaPhoto, CallbackQuery, Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.utils.callbacks import Knowledge, Cabinet, \
    Mailing, Category, CategoryCreate, Start, \
    CategoryRename, CategoryDelete, CategoryContent, CategoryClean, Info, Contacts
from shared.utils.config import settings
from shared.utils.db import db


def calculate_subscription_info(subscribed_date: float, subscribed_period: int):
    """
    Info about the subscription.
    :param subscribed_date: The timestamp when the subscription started
    :param subscribed_period: Subscription period in months
    :return: (remaining_days, end_time_msk) - remaining days and formatted end time
    """
    moscow_tz = timezone(timedelta(hours=3))
    utc_now = datetime.now(tz=timezone.utc)

    subscribe_datetime = datetime.fromtimestamp(subscribed_date, tz=timezone.utc)

    end_datetime_utc = subscribe_datetime + relativedelta(months=subscribed_period)

    end_datetime_msk = end_datetime_utc.astimezone(moscow_tz)

    remaining_days = max((end_datetime_utc - utc_now).days, 0)

    end_time_msk = end_datetime_msk.strftime('%Y-%m-%d %H:%M:%S')

    return remaining_days, end_time_msk


async def category_buttons(category,
                           user_id,
                           locale,
                           current_category,
                           parent_category) -> InlineKeyboardMarkup:
    """
    Category buttons.
    :param parent_category:
    :param current_category:
    :param category:
    :param user_id:
    :param locale:
    :return: keyboard
    """
    keyboard_category = InlineKeyboardBuilder()
    if category:
        for item in category:
            keyboard_category.row(
                InlineKeyboardButton(
                    text=item.name,
                    callback_data=Category(
                        current_id=item.id,
                        parent_id=item.parent_id).pack()))
    if user_id in settings.ADMIN_IDS:
        keyboard_category.row(
            InlineKeyboardButton(
                text=locale.categoryadd(),
                callback_data=CategoryCreate(
                    parent_id=current_category).pack()))
        keyboard_category.row(
            InlineKeyboardButton(
                text=locale.category.content(),
                callback_data=CategoryContent(
                    parent_id=parent_category,
                    current_id=current_category).pack()))
        keyboard_category.row(
            InlineKeyboardButton(
                text=locale.category.rename(),
                callback_data=CategoryRename(
                    current_id=current_category,
                    parent_id=parent_category).pack()))
        keyboard_category.row(
            InlineKeyboardButton(
                text=locale.category.clean(),
                callback_data=CategoryClean(
                    current_id=current_category,
                    parent_id=parent_category).pack()))
        keyboard_category.row(
            InlineKeyboardButton(
                text=locale.category.delete(),
                callback_data=CategoryDelete(
                    current_id=current_category,
                    parent_id=parent_category).pack()))

    if parent_category in [None, "Menu"]:
        if current_category in [None, "Info", "Contacts", "Knowledge"]:
            keyboard_category.row(
                InlineKeyboardButton(
                    text=locale.backbutton(),
                    callback_data=Start().pack()))
        else:
            keyboard_category.row(
                InlineKeyboardButton(
                    text=locale.backbutton(),
                    callback_data=Knowledge().pack()))


    else:
        res = await db.category.find_one({"id": parent_category})
        parent_id = res.parent_id if res else None
        keyboard_category.row(
            InlineKeyboardButton(
                text=locale.backbutton(),
                callback_data=Category(
                    current_id=parent_category,
                    parent_id=parent_id).pack()))
        keyboard_category.row(
            InlineKeyboardButton(
                text=locale.back_main_button(),
                callback_data=Knowledge().pack()))

    return keyboard_category.as_markup()


async def generate_unique_category_id() -> str:
    """
    Generate a unique category ID.
    :param db:
    :return:
    """
    while True:
        category_id = str(uuid.uuid4())[:5]
        existing_category = await db.category.find_one({'id': category_id})
        if not existing_category:
            return category_id


async def generate_unique_order_id() -> int:
    """
    Unique order id

    :param db: MongoDbClient.
    :return: order_id
    """
    while True:
        order_id = random.randint(1, 2147483647)
        existing_transaction = await db.transactions.find_one({"order_id": order_id})
        if not existing_transaction:
            return order_id


def build_menu_keyboard(locale, user_id: int, admin_ids: List[int]) -> InlineKeyboardMarkup:
    """
    Creates a menu keyboard depending on the user's role.

    :param locale: Localization object for button texts.
    :param user_id: The ID of the user for whom the keyboard is being created.
    :param admin_ids: A list of administrator IDs.
    :return: An InlineKeyboardMarkup object with the keyboard layout.
    """
    keyboard_menu = InlineKeyboardBuilder()

    # Add general menu buttons
    keyboard_menu.row(InlineKeyboardButton(
        text=locale.menubutton1(),
        callback_data=Knowledge().pack()))
    keyboard_menu.add(InlineKeyboardButton(
        text=locale.menubutton2(),
        callback_data=Cabinet().pack()))
    keyboard_menu.row(InlineKeyboardButton(
        text=locale.menubutton3(),
        callback_data=Info().pack()))
    keyboard_menu.add(InlineKeyboardButton(
        text=locale.menubutton4(),
        callback_data=Contacts().pack()))

    # Add admin-specific button if the user is an admin
    if user_id in admin_ids:
        keyboard_menu.row(
            InlineKeyboardButton(
                text=locale.menubutton_admin(),
                callback_data=Mailing().pack()))

    return keyboard_menu.as_markup()


async def check_subscription(user_id):
    """
    Check subscription status.
    :param user_id:
    :return:
    """
    user = await db.users.find_one({"id": user_id})
    if user.subscribed:
        if user.subscribed_date < time.time() - user.subscribed_period * 30.44 * 24 * 60 * 60:
            await db.users.update_one({"id": user_id}, {"subscribed": False,
                                                        "subscribed_period": None,
                                                        "subscribed_date": None})
            return False
        return True


async def subscription_offer(bot, user_id, locale, message_id):
    """
    Subscription offer.
    :param bot:
    :param user_id:
    :param locale:
    :param message_id:
    :return:
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=locale.menubutton2(), callback_data=Cabinet().pack()))
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data=Start().pack()))
    await bot.edit_message_caption(chat_id=user_id,
                                   caption=locale.subscription.offer(),
                                   message_id=message_id,
                                   reply_markup=keyboard.as_markup())


async def send_category_content(bot, message: Union[Message, CallbackQuery],

                                current_id: str, locale):  # pylint: disable=all
    # I have no time for optimize this func my deadlines in fire
    """
    Отправляет контент категории
    :param bot: объект бота
    :param message: сообщение или callback
    :param current_id: ID текущей категории
    :param locale: объект локализации
    """
    category = await db.category.find_one({"id": current_id})
    category_next = await db.category.find({"parent_id": current_id})
    keyboard = await category_buttons(category_next, message.from_user.id,
                                      locale, current_id,
                                      category.parent_id if category else None)
    message_ids = []

    if isinstance(message, CallbackQuery):
        await bot.delete_message(
            chat_id=message.from_user.id,
            message_id=message.message.message_id
        )

    media_fields_order = ['photos', 'videos', 'documents', 'audios', 'voices', 'video_notes']

    for field in media_fields_order:
        if category and hasattr(category, field) and getattr(category, field):
            media_list = getattr(category, field)
            print(f"🔥 {field.upper()} DETECTED, SENDING...")

            if media_list[0].type == "media_group":
                if field == 'photos':
                    media_group = [
                        InputMediaPhoto(media=file_id) for file_id in media_list[0].file_id]
                elif field == 'videos':
                    media_group = [
                        InputMediaVideo(media=file_id) for file_id in media_list[0].file_id]
                elif field == 'audios':
                    media_group = [
                        InputMediaAudio(media=file_id) for file_id in media_list[0].file_id]
                elif field == 'documents':
                    media_group = [
                        InputMediaDocument(media=file_id) for file_id in media_list[0].file_id]
                else:
                    continue

                messages = await bot.send_media_group(
                    chat_id=message.from_user.id,
                    media=media_group
                )
                message_ids.extend([msg.message_id for msg in messages])

            else:
                res = None

                if field == 'photos':
                    res = await bot.send_photo(
                        chat_id=message.from_user.id,
                        photo=media_list[0].file_id[0])
                elif field == 'videos':
                    res = await bot.send_video(
                        chat_id=message.from_user.id,
                        video=media_list[0].file_id[0])
                elif field == 'audios':
                    res = await bot.send_audio(
                        chat_id=message.from_user.id,
                        audio=media_list[0].file_id[0])
                elif field == 'documents':
                    res = await bot.send_document(
                        chat_id=message.from_user.id,
                        document=media_list[0].file_id[0])
                elif field == 'voices':
                    print("Отправляю voice")
                    try:
                        res = await bot.send_voice(chat_id=message.from_user.id, voice=media_list[0].file_id[0])
                    except TelegramBadRequest:
                        try:
                            await bot.send_audio(chat_id=message.from_user.id, audio=media_list[0].file_id[0])
                        except TelegramBadRequest:
                            res = await bot.send_message(
                                chat_id=message.from_user.id,
                                text="Извините, не могу прислать вам голосовое сообщение,"
                                     " проверьте настройки конфиденциальности!")
                        else:
                            raise
                elif field == "video_notes":
                    res = await bot.send_video_note(
                        chat_id=message.from_user.id,
                        video_note=media_list[0].file_id[0])

                if res:
                    message_ids.append(res.message_id)

    await db.users.update_one(
        {"id": message.from_user.id},
        {"message_ids": message_ids}
    )

    caption = (
        category.caption
        if (category
            and hasattr(category, 'caption')
            and category.caption)
        else "No caption"
    )
    await bot.send_message(
        chat_id=message.from_user.id,
        text=caption,
        reply_markup=keyboard
    )
