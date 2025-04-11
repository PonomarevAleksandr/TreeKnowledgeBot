"""FSM STATES"""
from aiogram.fsm.state import StatesGroup, State


class CategoryName(StatesGroup): # pylint: disable=too-few-public-methods
    """[ADMIN] Category name"""
    category_name = State()
    category_rename = State()

class CategoryMedia(StatesGroup): # pylint: disable=too-few-public-methods
    """[ADMIN] Category media"""
    category_media = State()

class MailingAll(StatesGroup): # pylint: disable=too-few-public-methods
    """[ADMIN] Mailing"""
    mailing_send = State()

class ChangePriceState(StatesGroup): # pylint: disable=too-few-public-methods
    """[ADMIN] ChangePrice"""
    change_price = State()


class PromoActivateState(StatesGroup): # pylint: disable=too-few-public-methods
    """[USER] ChangePrice"""
    promo_enter = State()


class DiscountCreateState(StatesGroup): # pylint: disable=too-few-public-methods
    """[USER] Discount create"""
    discount_name = State()
    discount_price = State()
