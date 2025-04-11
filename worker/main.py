"""Payment worker"""
import asyncio
import logging
import time

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from aiogram.types import InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from shared.utils.callbacks import Start, Cabinet
from shared.utils.check_payment import check_payment_status

from shared.utils.config import settings
from shared.utils.db import db

bot_token = settings.BOT_TOKEN
bot = Bot(token=bot_token)
logging.basicConfig(level=logging.INFO)


async def check_transactions():
    """
    Check payment status
    :return: None
    """
    logging.info("Transactions check started...")
    while True:
        current_time = time.time()
        orders_to_check = await db.transactions.find({})
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="Назад", callback_data=Start().pack()))

        for order in orders_to_check:
            logging.info("Transactions : %s", orders_to_check)
            payment_status = await check_payment_status(
                settings.ROBOKASSA_LOGIN,
                order.order_id,
                settings.ROBOKASSA_PASSWORD_2
            )

            if payment_status == 100:
                logging.info("Payment complete : %s", order.order_id)
                await db.order_history.insert_one({
                    "order_id": order.order_id,
                    "created_at": current_time
                })
                await db.users.update_one(
                    {"id": order.user_id},
                    {
                        "subscribed": True,
                        "subscribed_date": current_time,
                        "subscribed_period": order.period
                    }
                )

                await bot.edit_message_caption(
                    chat_id=order.user_id,
                    message_id=order.message_id,
                    caption="Ваш платеж прошел успешно!",
                    reply_markup=keyboard.as_markup()
                )

                await db.transactions.delete_one(
                    {"order_id": order.order_id}
                )

            else:
                if current_time - order.created_at > 3600:
                    await db.transactions.delete_one({"order_id": order.order_id})

                    try:
                        await bot.edit_message_caption(
                            chat_id=order.user_id,
                            message_id=order.message_id,
                            caption="Извините, подписка не была оплачена.",
                            reply_markup=keyboard.as_markup()
                        )
                    except TelegramBadRequest as e:
                        logging.error(f"BadRequest: {e} : %s", order.order_id)
                    except TelegramRetryAfter as e:
                        logging.error(f"RetryAfter: {e} : %s", order.order_id)
                        await asyncio.sleep(e.retry_after)
                    logging.info("Transaction deleted (1hour timeout) : %s", order.order_id)
                logging.info("Transaction is not completed yet: %s", order.order_id)

        await asyncio.sleep(10)


async def subscription_notification():
    """
    subscription notification
    :return:
    """
    logging.info("Subscription notification started...")
    while True:
        print(f"current time: {time.time()}")
        all_users = await db.users.find({})

        for user in all_users:
            if not user.subscribed:
                continue

            subscribed_date = user.subscribed_date
            subscribed_period = user.subscribed_period

            if not subscribed_date or not subscribed_period:
                continue

            subscription_end = subscribed_date + (subscribed_period * 30 * 24 * 60 * 60)
            time_left = subscription_end - time.time()

            if time_left <= 0:
                keyboard = InlineKeyboardBuilder()
                keyboard.row(InlineKeyboardButton(text="👤 Подписка", callback_data=Cabinet().pack()))
                await bot.send_photo(chat_id=user.id,
                                     photo=FSInputFile(
                                         "welcome.jpg", filename="welcome.jpg"),
                                     caption=f'ПОДПИСКА НЕ ОФОРМЛЕНА!\n'
                                             'База знаний "Юрист Бьюти Бот" недоступна!\n'
                                             '⚜️Для активации сервиса, пожалуйста, перейдите в раздел "Подписка" в меню ниже',
                                     reply_markup=keyboard.as_markup())
                await db.users.update_one({"id": user.id}, {"subscribed": False,
                                                            "subscribed_date": None,
                                                            "subscribed_period": None})
        await asyncio.sleep(120)


async def main():
    """
    Async main function
    """
    logging.info("Starting workers")

    await asyncio.gather(
        check_transactions(),
        subscription_notification()
    )


if __name__ == "__main__":
    asyncio.run(main())
