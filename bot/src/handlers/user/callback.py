"""User callback handlers """
import decimal
import time

from aiogram import types, Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from shared.utils.callbacks import (Knowledge,
                                    Cabinet, SubscriptionPeriod,
                                    SubscriptionInvoice, Start,
                                    Category, SubscriptionSettings, PromoActivate, Contacts, Info)
from shared.utils.fsm_state import PromoActivateState
from shared.utils.functions import (calculate_subscription_info,
                                    generate_unique_order_id, build_menu_keyboard,
                                    send_category_content, subscription_offer)
from shared.utils.robokassa import PaymentData, generate_payment_link, RobokassaConfig

from shared.utils.config import settings
from shared.utils.db import MongoDbClient

router = Router()


@router.callback_query(Start.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            state: FSMContext,
            locale: TranslatorRunner):
    await callback_query.answer(locale.backbutton())
    keyboard_menu = build_menu_keyboard(
        locale=locale,
        user_id=callback_query.from_user.id,
        admin_ids=settings.ADMIN_IDS
    )
    await bot.delete_message(chat_id=callback_query.from_user.id,
                             message_id=callback_query.message.message_id)
    await bot.send_photo(chat_id=callback_query.from_user.id,
                         photo=FSInputFile("src/assets/welcome.jpg",
                                           filename="welcome.jpg"),
                         caption=locale.text.welcome(),
                         reply_markup=keyboard_menu)
    await state.clear()


@router.callback_query(Contacts.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            locale: TranslatorRunner):
    category = await db.category.find({"id": "Contacts"})
    if category:
        # pylint: disable=duplicate-code
        await send_category_content(
            bot=bot,
            message=callback_query,
            current_id="Contacts",
            locale=locale
        )
    else:
        await db.category.insert_one({"id": "Contacts"})
        # pylint: disable=duplicate-code
        await send_category_content(
            bot=bot,
            message=callback_query,
            current_id="Contacts",
            locale=locale
        )


@router.callback_query(Info.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            locale: TranslatorRunner):
    category = await db.category.find({"id": "Info"})
    if category:
        # pylint: disable=duplicate-code
        await send_category_content(
            bot=bot,
            message=callback_query,
            current_id="Info",
            locale=locale
        )
    else:
        await db.category.insert_one({"id": "Info"})
        # pylint: disable=duplicate-code
        await send_category_content(
            bot=bot,
            message=callback_query,
            current_id="Info",
            locale=locale
        )


# Knowledge section
@router.callback_query(Knowledge.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            locale: TranslatorRunner):
    await callback_query.answer(locale.menubutton1())
    user = await db.users.find_one({"id": callback_query.from_user.id})
    if user.subscribed:

        category = await db.category.find({"id": "Knowledge"})
        if category:
            # pylint: disable=duplicate-code
            await send_category_content(
                bot=bot,
                message=callback_query,
                current_id="Knowledge",
                locale=locale
            )
        else:
            await db.category.insert_one({"id": "Knowledge"})
            # pylint: disable=duplicate-code
            await send_category_content(
                bot=bot,
                message=callback_query,
                current_id="Knowledge",
                locale=locale
            )
    else:
        await subscription_offer(bot, callback_query.from_user.id, locale, callback_query.message.message_id)


@router.callback_query(Category.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            callback_data: Category,
            locale: TranslatorRunner):
    await callback_query.answer(locale.category.open())
    # pylint: disable=duplicate-code
    await send_category_content(
        bot=bot,
        message=callback_query,
        current_id=callback_data.current_id,
        locale=locale
    )


# Cabinet section
@router.callback_query(Cabinet.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            locale: TranslatorRunner):
    await callback_query.answer(locale.menubutton2())
    res = await db.users.find_one({"id": callback_query.from_user.id})
    keyboard_info = InlineKeyboardBuilder()
    if res.subscribed:
        remaining_days, end_time = calculate_subscription_info(
            subscribed_date=res.subscribed_date,
            subscribed_period=res.subscribed_period
        )
        caption = locale.subscription.subscribed(remaining_days=remaining_days,
                                                 end_time=end_time)
    else:
        caption = locale.subscription.unsubscribed()
        keyboard_info.row(
            InlineKeyboardButton(
                text=locale.buybutton(),
                callback_data=SubscriptionPeriod().pack()))
    if callback_query.from_user.id in settings.ADMIN_IDS:
        keyboard_info.row(
            InlineKeyboardButton(
                text="Настройка",
                callback_data=SubscriptionSettings().pack()
            )
        )
    keyboard_info.row(
        InlineKeyboardButton(
            text=locale.backbutton(),
            callback_data=Start().pack()))
    await bot.edit_message_caption(chat_id=callback_query.from_user.id,
                                   message_id=callback_query.message.message_id,
                                   caption=caption,
                                   reply_markup=keyboard_info.as_markup())


# Subscription section
@router.callback_query(SubscriptionPeriod.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            locale: TranslatorRunner,
            db: MongoDbClient):
    await callback_query.answer(locale.buybutton())
    keyboard_period = InlineKeyboardBuilder()
    config = await db.config_admin.find_one({"id": 1})
    if config is None:
        await db.config_admin.insert_one({"id": 1,
                                          "one_month": 1.00,
                                          "three_month": 1.00,
                                          "half_year": 1.00,
                                          "year": 1.00})
        config = await db.config_admin.find_one({"id": 1})
    personal_discounts = await db.users.find_one({"id": callback_query.from_user.id})
    if personal_discounts.personal_month:
        price_month = personal_discounts.personal_month
    else:
        price_month = config.one_month
    if personal_discounts.personal_three_month:
        price_three_month = personal_discounts.personal_three_month
    else:
        price_three_month = config.three_month
    if personal_discounts.personal_half_year:
        price_half_year = personal_discounts.personal_half_year
    else:
        price_half_year = config.half_year
    if personal_discounts.personal_year:
        price_year = personal_discounts.personal_year
    else:
        price_year = config.year
    periods = [
        (1, locale.month(), price_month),
        (3, locale.three_month(), price_three_month),
        (6, locale.halfyear(), price_half_year),
        (12, locale.year(), price_year)
    ]
    print(f"periods: {periods}")
    for period, text, price in periods:
        keyboard_period.row(
            InlineKeyboardButton(
                text=text,
                callback_data=SubscriptionInvoice(period=period, price=price).pack()))
    keyboard_period.row(
        InlineKeyboardButton(
            text="Промокод",
            callback_data=PromoActivate().pack()))
    if callback_query.from_user.id in settings.ADMIN_IDS:
        keyboard_period.row(
            InlineKeyboardButton
                (
                text="Настройка",
                callback_data=SubscriptionSettings().pack()
            )
        )
    keyboard_period.row(
        InlineKeyboardButton(
            text=locale.backbutton(),
            callback_data=Cabinet().pack()))

    await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption=locale.subscription.price(one_month=int(price_month),
                                          three_month=int(price_three_month),
                                          half_year=int(price_half_year),
                                          year=int(price_year)),
        reply_markup=keyboard_period.as_markup())


@router.callback_query(SubscriptionInvoice.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            db: MongoDbClient,
            callback_data: SubscriptionInvoice,
            locale: TranslatorRunner):
    await callback_query.answer(locale.buybutton())
    await db.users.update_one({"id": callback_query.from_user.id},
                              {"personal_month": None,
                               "personal_three_month": None,
                               "personal_half_year": None,
                               "personal_year": None})
    order_id = await generate_unique_order_id()
    robokassa_config = RobokassaConfig(
        merchant_login=settings.ROBOKASSA_LOGIN,
        merchant_password_1=settings.ROBOKASSA_PASSWORD_1)
    payment = PaymentData(
        config=robokassa_config,
        cost=decimal.Decimal(callback_data.price),
        number=order_id,
        description=locale.subscription.description(period=callback_data.period),
        user_id=callback_query.from_user.id,
        period=callback_data.period)
    payment_link = await generate_payment_link(payment)
    keyboard_link = InlineKeyboardBuilder()
    keyboard_link.row(
        InlineKeyboardButton(
            text=locale.paybutton(),
            url=payment_link))
    keyboard_link.row(
        InlineKeyboardButton(
            text=locale.backbutton(),
            callback_data=SubscriptionPeriod().pack()))
    await bot.edit_message_caption(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        caption=locale.subscription.pay(period_subscription=callback_data.period,
                                        price_subscription=callback_data.price),
        reply_markup=keyboard_link.as_markup())
    await db.transactions.insert_one({
        "order_id": order_id,
        "user_id": callback_query.from_user.id,
        "period": int(callback_data.period),
        "message_id": callback_query.message.message_id,
        "created_at": time.time()
    })


@router.callback_query(PromoActivate.filter())
async def _(callback_query: types.CallbackQuery,
            bot: Bot,
            state: FSMContext):
    await callback_query.answer("Промокод")
    await state.update_data(message_id=callback_query.message.message_id)
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data=Cabinet().pack()))
    await bot.edit_message_caption(chat_id=callback_query.from_user.id,
                                   message_id=callback_query.message.message_id,
                                   caption="Введите промокод",
                                   reply_markup=keyboard.as_markup())
    await state.set_state(PromoActivateState.promo_enter)
