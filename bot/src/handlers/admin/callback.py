"""Admin callback handlers"""
import time
import uuid

from aiogram import Router, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from shared.utils.functions import send_category_content
from shared.utils.functions_admin import keyboard_back

from shared.utils.callbacks import (CategoryCreate, CategoryDelete, \
                                    CategoryRename, CategoryContent, CategoryClean, Mailing, Start,
                                    SendMailing, CategoryCleanFinish, CategoryBack, \
                                    SubscriptionSettings, ChangePrice, Cabinet, PromoCreate,
                                    DiscountsCallback, DiscountsFinish)
from shared.utils.db import MongoDbClient
from shared.utils.fsm_state import (CategoryName, CategoryMedia, MailingAll,
                                    ChangePriceState, DiscountCreateState)

router = Router()


@router.callback_query(CategoryCreate.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            state: FSMContext,
            callback_data: CategoryCreate,
            locale: TranslatorRunner):
    await callback_query.answer(locale.categoryadd())
    await bot.delete_message(chat_id=callback_query.message.chat.id,
                             message_id=callback_query.message.message_id)
    res = await bot.send_message(chat_id=callback_query.from_user.id,
                                 text=locale.category.name())
    await state.set_state(CategoryName.category_name)
    await state.update_data(parent_id=callback_data.parent_id,
                            message_id=res.message_id)


@router.callback_query(CategoryDelete.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            callback_data: CategoryDelete,
            locale: TranslatorRunner):
    await callback_query.answer(locale.category.delete())
    await db.category.delete_one({"id": callback_data.current_id})
    keyboard = await keyboard_back(callback_data.parent_id, locale)
    await bot.edit_message_media(chat_id=callback_query.from_user.id,
                                 message_id=callback_query.message.message_id,
                                 media=InputMediaPhoto(
                                     media=FSInputFile("src/assets/no_image.png"),
                                     caption=locale.category.deleted()),
                                 reply_markup=keyboard)


@router.callback_query(CategoryRename.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            state: FSMContext,
            callback_data: CategoryRename,
            locale: TranslatorRunner):
    await callback_query.answer(locale.category.rename())
    await bot.edit_message_text(chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id,
                                text=locale.category.name())
    await state.set_state(CategoryName.category_rename)
    await state.update_data(current_id=callback_data.current_id,
                            parent_id=callback_data.parent_id,
                            message_id=callback_query.message.message_id)


@router.callback_query(CategoryContent.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            state: FSMContext,
            callback_data: CategoryContent,
            locale: TranslatorRunner):
    await callback_query.answer(locale.category.content())
    await bot.delete_message(chat_id=callback_query.from_user.id,
                             message_id=callback_query.message.message_id)
    res = await bot.send_message(chat_id=callback_query.from_user.id,
                                 text=locale.category.content_upload())
    await state.set_state(CategoryMedia.category_media)
    await state.update_data(current_id=callback_data.current_id,
                            parent_id=callback_data.parent_id,
                            message_id=res.message_id)


@router.callback_query(CategoryClean.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            callback_data: CategoryContent,
            locale: TranslatorRunner):
    await callback_query.answer(locale.category.clean())
    keyboard = InlineKeyboardBuilder()
    category = await db.category.find_one({"id": callback_data.current_id})
    if category.photos:
        keyboard.row(InlineKeyboardButton(
            text="Фото",
            callback_data=CategoryCleanFinish(current_id=callback_data.current_id,
                                              parent_id=callback_data.parent_id,
                                              type="photos").pack()))
    if category.videos:
        keyboard.row(InlineKeyboardButton(
            text="Видео",
            callback_data=CategoryCleanFinish(current_id=callback_data.current_id,
                                              parent_id=callback_data.parent_id,
                                              type="videos").pack()
        ))
    if category.audios:
        keyboard.row(InlineKeyboardButton(
            text="Аудио",
            callback_data=CategoryCleanFinish(current_id=callback_data.current_id,
                                              parent_id=callback_data.parent_id,
                                              type="audios").pack()
        ))
    if category.documents:
        keyboard.row(InlineKeyboardButton(
            text="Документы",
            callback_data=CategoryCleanFinish(current_id=callback_data.current_id,
                                              parent_id=callback_data.parent_id,
                                              type="documents").pack()
        ))
    if category.voices:
        keyboard.row(InlineKeyboardButton(
            text="Голосовые сообщения",
            callback_data=CategoryCleanFinish(current_id=callback_data.current_id,
                                              parent_id=callback_data.parent_id,
                                              type="voices").pack()
        ))
    if category.video_notes:
        keyboard.row(InlineKeyboardButton(
            text="Кружки",
            callback_data=CategoryCleanFinish(current_id=callback_data.current_id,
                                              parent_id=callback_data.parent_id,
                                              type="video_notes").pack()
        ))
    keyboard.row(InlineKeyboardButton(
        text="Полная очистка",
        callback_data=CategoryCleanFinish(current_id=callback_data.current_id,
                                          parent_id=callback_data.parent_id,
                                          type="all").pack())
    )
    keyboard.row(InlineKeyboardButton(
        text="Назад",
        callback_data=CategoryBack(current_id=callback_data.current_id).pack()
    ))
    await bot.delete_message(chat_id=callback_query.from_user.id,
                             message_id=callback_query.message.message_id)
    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="Выберите контент для удаления:",
                           reply_markup=keyboard.as_markup())


@router.callback_query(CategoryCleanFinish.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            callback_data: CategoryCleanFinish,
            locale: TranslatorRunner):
    if callback_data.type == "all":
        await db.category.update_one({"id": callback_data.current_id},
                                     {"photos": [],
                                      "videos": [],
                                      "audios": [],
                                      "documents": [],
                                      "voices": [],
                                      "video_notes": [],
                                      "messages": [],
                                      "caption": None,
                                      "updated_at": time.time()})
    else:
        await db.category.update_one({"id": callback_data.current_id},
                                     {callback_data.type: []})
    await callback_query.answer(text="Удаление прошло успешно", show_alert=True)
    await keyboard_back(callback_data.parent_id, locale)
    await send_category_content(
        bot=bot,
        message=callback_query,
        current_id=callback_data.current_id,
        locale=locale,
    )


@router.callback_query(CategoryBack.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            callback_data: CategoryBack,
            locale: TranslatorRunner):
    # pylint: disable=duplicate-code
    await send_category_content(
        bot=bot,
        message=callback_query,
        current_id=callback_data.current_id,
        locale=locale,
    )


@router.callback_query(Mailing.filter())
async def mailing_start(callback_query: CallbackQuery,
                        state: FSMContext,
                        locale: TranslatorRunner,
                        bot: Bot):
    """
    Mailing callback
    :param callback_query:
    :param state:
    :param locale:
    :param bot:
    :return:
    """
    await callback_query.answer(locale.menubutton_admin())
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text=locale.backbutton(),
        callback_data=Start().pack()))
    mes = await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        caption=locale.mailing.input_text(),
        message_id=callback_query.message.message_id,
        reply_markup=keyboard.as_markup())
    await state.set_state(MailingAll.mailing_send)
    await state.update_data(message_id=mes.message_id)


@router.callback_query(SendMailing.filter())
async def send_all_confirm(callback_query: CallbackQuery,
                           db: MongoDbClient,
                           callback_data: SendMailing,
                           locale: TranslatorRunner,
                           bot: Bot):
    """
    Mailing send
    :param callback_query:
    :param db:
    :param callback_data:
    :param locale:
    :param bot:
    :return:
    """
    await callback_query.answer(locale.confirm())
    await bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id)
    users = await db.users.find({}, count=10000000)
    users_list = [{'id': user.id} for user in users]
    successful_sends = 0
    failed_sends = 0
    mes = await bot.send_message(
        chat_id=callback_query.from_user.id,
        text=locale.mailing.wait())
    for user in users_list:
        try:
            await bot.copy_message(
                chat_id=int(user['id']),
                from_chat_id=callback_query.from_user.id,
                message_id=int(callback_data.mes_id))
            successful_sends += 1
        except TelegramAPIError:
            failed_sends += 1
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text=locale.backbutton(),
        callback_data=Start().pack()))
    await bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=mes.message_id)
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text=locale.mailing.sent(total_users=len(users_list),
                                 successful_sends=successful_sends,
                                 failed_sends=failed_sends),
        reply_markup=keyboard.as_markup())


@router.callback_query(SubscriptionSettings.filter())
async def _(callback_query: CallbackQuery,
            db: MongoDbClient,
            bot: Bot):
    await callback_query.answer("Настройка")
    config = await db.config_admin.find_one({"id": 1})
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text="Месяц",
        callback_data=ChangePrice(period="one_month").pack()))
    keyboard.row(InlineKeyboardButton(
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
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption=f"<b>Актуальные цены:</b>\n"
                f"<b>1 месяц: </b>{int(config.one_month)}\n"
                f"<b>3 месяца: </b>{int(config.three_month)}\n"
                f"<b>6 месяцев: </b>{int(config.half_year)}\n"
                f"<b>12 месяцев: </b>{int(config.year)}\n\n"
                f"За какой период нужно изменить цены?",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(ChangePrice.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            callback_data: ChangePrice,
            state: FSMContext):
    await callback_query.answer("Изменить цену")
    await state.update_data(
        period=callback_data.period,
        message_id=callback_query.message.message_id)
    await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption="Введите цену (целое число) "
                "Пример: 1000"
    )
    await state.set_state(ChangePriceState.change_price)


@router.callback_query(PromoCreate.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            callback_data: PromoCreate):
    await callback_query.answer("Промокоды")
    keyboard = InlineKeyboardBuilder()
    if callback_data.period:
        if callback_data.usages:
            promo_code = uuid.uuid4().hex
            await db.promo_codes.insert_one({"promo_code": promo_code,
                                             "period": callback_data.period,
                                             "usages": callback_data.usages})
            text = f"Промокод успешно создан: \n<code>{promo_code}</code>"
        else:
            keyboard.row(
                InlineKeyboardButton(
                    text="1",
                    callback_data=PromoCreate(
                        usages=1,
                        period=callback_data.period).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="3",
                    callback_data=PromoCreate(
                        usages=3,
                        period=callback_data.period).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="5",
                    callback_data=PromoCreate(
                        usages=5,
                        period=callback_data.period).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="10",
                    callback_data=PromoCreate(
                        usages=10,
                        period=callback_data.period).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="100",
                    callback_data=PromoCreate(
                        usages=100,
                        period=callback_data.period).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="500",
                    callback_data=PromoCreate(
                        usages=500,
                        period=callback_data.period).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="1000",
                    callback_data=PromoCreate(
                        usages=1000,
                        period=callback_data.period).pack()))
            text = "Выберите кол-во использований"
    else:
        keyboard.row(
            InlineKeyboardButton(
                text="Месяц",
                callback_data=PromoCreate(period=1).pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="3 Месяца",
                callback_data=PromoCreate(period=3).pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="6 месяцев",
                callback_data=PromoCreate(period=6).pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="Год",
                callback_data=PromoCreate(period=12).pack()))
        text = "Выберите период"
    keyboard.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data=SubscriptionSettings().pack()))
    await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption=text,
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(DiscountsCallback.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            state: FSMContext):
    await callback_query.answer("Скидки")
    await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption="Введите промокод для скидки"
    )
    await state.update_data(message_id=callback_query.message.message_id)
    await state.set_state(DiscountCreateState.discount_name)


@router.callback_query(DiscountsFinish.filter())
async def _(callback_query: CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            callback_data: DiscountsFinish,
            state: FSMContext):
    await callback_query.answer(text="Скидки")
    keyboard = InlineKeyboardBuilder()
    if callback_data.to_period:
        if callback_data.period:
            await state.update_data(discount=callback_data.discount,
                                    message_id=callback_query.message.message_id)
            await db.discounts.update_one(
                {"promo_code": callback_data.discount.lower()},
                {"to_period": callback_data.to_period,
                 "period": callback_data.period,
                 "created_at": time.time()}, upsert=True)
            await state.set_state(DiscountCreateState.discount_price)
            await bot.edit_message_caption(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                caption=f"Введите цену по скидке для периода в "
                        f"{callback_data.to_period} мес."
            )
        else:
            keyboard.row(
                InlineKeyboardButton(
                    text="1 день",
                    callback_data=DiscountsFinish(
                        discount=callback_data.discount,
                        to_period=callback_data.to_period,
                        period=1).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="3 дня",
                    callback_data=DiscountsFinish(
                        discount=callback_data.discount,
                        to_period=callback_data.to_period,
                        period=3).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="7 дней",
                    callback_data=DiscountsFinish(
                        discount=callback_data.discount,
                        to_period=callback_data.to_period,
                        period=7).pack()))
            keyboard.row(
                InlineKeyboardButton(
                    text="30 дней",
                    callback_data=DiscountsFinish(
                        discount=callback_data.discount,
                        to_period=callback_data.to_period,
                        period=30).pack()))
            await bot.edit_message_caption(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                caption="Выберите срок действия скидки:",
                reply_markup=keyboard.as_markup()
            )
    else:
        keyboard.row(
            InlineKeyboardButton(
                text="1 месяц",
                callback_data=DiscountsFinish(
                    discount=callback_data.discount,
                    to_period=1).pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="3 месяца",
                callback_data=DiscountsFinish(
                    discount=callback_data.discount,
                    to_period=3).pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="6 месяцев",
                callback_data=DiscountsFinish(
                    discount=callback_data.discount,
                    to_period=6).pack()))
        keyboard.row(
            InlineKeyboardButton(
                text="12 месяцев",
                callback_data=DiscountsFinish(
                    discount=callback_data.discount,
                    to_period=12).pack()))
        await bot.edit_message_caption(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            caption="Выберите период на который будет действовать скидка:",
            reply_markup=keyboard.as_markup()
        )
