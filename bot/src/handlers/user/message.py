"""User message handlers"""
import time

from aiogram import types, Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from shared.utils.callbacks import Cabinet
from shared.utils.db import MongoDbClient
from shared.utils.fsm_state import PromoActivateState
from shared.utils.functions import build_menu_keyboard
from shared.utils.config import settings

router = Router()


@router.message(Command("start"))
async def _(message: types.Message, bot: Bot, locale: TranslatorRunner):
    keyboard_menu = build_menu_keyboard(
        locale=locale,
        user_id=message.from_user.id,
        admin_ids=settings.ADMIN_IDS,
    )

    await bot.send_photo(chat_id=message.from_user.id,
                         photo=FSInputFile(
                             "src/assets/welcome.jpg", filename="welcome.jpg"),
                         caption=locale.text.welcome(),
                         reply_markup=keyboard_menu)


@router.message(PromoActivateState.promo_enter)
async def _(message: types.Message,
            bot: Bot,
            state: FSMContext,
            db: MongoDbClient,):
    await bot.delete_message(chat_id=message.from_user.id,
                             message_id=message.message_id)
    keyboard = InlineKeyboardBuilder()
    data = await state.get_data()
    message_id = data.get("message_id")
    promo_code = await db.promo_codes.find_one({"promo_code": message.text})
    if promo_code:
        if promo_code.usages >= 1:
            await db.users.update_one({"id": message.from_user.id},
                                      {"subscribed_date": time.time(),
                                       "subscribed": True,
                                       "subscribed_period": promo_code.period})
            caption = "Промокод успешно активирован!"
            await db.promo_codes.update_one({"promo_code": message.text},
                                            {"usages": int(promo_code.usages - 1)})
        else:
            await db.promo_codes.delete_one({"promo_code": message.text})
            caption = "Извините, этот промокод истек"
        keyboard.row(InlineKeyboardButton(text="Назад", callback_data=Cabinet().pack()))
        await bot.edit_message_caption(
            chat_id=message.from_user.id,
            message_id=message_id,
            caption=caption,
            reply_markup=keyboard.as_markup()
        )
    else:
        discount = await db.discounts.find_one({"promo_code": message.text.lower()})
        if discount:
            time_passed_seconds = time.time() - discount.created_at
            time_passed_days = time_passed_seconds / (24 * 60 * 60)

            if time_passed_days > discount.period:
                keyboard.row(InlineKeyboardButton(text="Назад", callback_data=Cabinet().pack()))
                await bot.edit_message_caption(
                    chat_id=message.from_user.id,
                    message_id=message_id,
                    caption="⚠️ Срок действия промокода истек!",
                    reply_markup=keyboard.as_markup()
                )
                return


            if discount.to_period == 1:
                period_type = "personal_month"
            elif discount.to_period == 3:
                period_type = "personal_three_month"
            elif discount.to_period == 6:
                period_type = "personal_half_year"
            else:
                period_type = "personal_year"


            await db.users.update_one(
                {"id": message.from_user.id},
                {period_type: float(discount.price)}
            )

            keyboard.row(InlineKeyboardButton(text="Назад", callback_data=Cabinet().pack()))
            await bot.edit_message_caption(
                chat_id=message.from_user.id,
                message_id=message_id,
                caption=f"✅ Скидка активирована!\n"
                        f"Персональная цена установлена:\n"
                        f"{discount.to_period} мес - {int(discount.price)} руб!",
                reply_markup=keyboard.as_markup()
            )
        else:

            caption = "Промокод не найден"
            keyboard.row(InlineKeyboardButton(text="Назад", callback_data=Cabinet().pack()))
            await bot.edit_message_caption(
                chat_id=message.from_user.id,
                message_id=message_id,
                caption=caption,
                reply_markup=keyboard.as_markup()
            )
    await state.clear()
