"""Callbacks for keyboards"""
from typing import Optional

from aiogram.filters.callback_data import CallbackData


class Start(CallbackData, prefix='start'):
    """
    [USER] Start bot callback
    """


class Info(CallbackData, prefix='info'):
    """
    [USER] Start bot callback
    """

class Contacts(CallbackData, prefix='contacts'):
    """
    [USER] Start bot callback
    """


class Knowledge(CallbackData, prefix='Knowledge'):
    """
    [USERS] Knowledge callback
    """
    current_id: Optional[str] = None
    parent_id: Optional[str] = "Menu"


class Cabinet(CallbackData, prefix='cabinet'):
    """
    [USERS] Cabinet callback
    """


class SubscriptionPeriod(CallbackData, prefix='subscription_period'):
    """
    [USER] Buy subscription callback
    """


class SubscriptionInvoice(CallbackData, prefix='subscription_invoice'):
    """
    [USER] Buy subscription callback
    """
    period: int
    price: float


class SubscriptionSettings(CallbackData, prefix='subscription_settings'):
    """
    [Admin] Buy subscription callback
    """


class ChangePrice(CallbackData, prefix='change_price'):
    """
    [Admin] Change price callback
    """
    period: str


class PromoCreate(CallbackData, prefix='promo_create'):
    """
    [Admin] Change price callback
    """
    usages: Optional[int] = None
    period: Optional[int] = None


class PromoActivate(CallbackData, prefix='promo_create'):
    """
    [User] Promo activate callback
    """


class DiscountsCallback(CallbackData, prefix='discounts'):
    """
    [ADMIN] Promo activate callback
    """


class DiscountsFinish(CallbackData, prefix='discounts_finish'):
    """
    [ADMIN] Promo activate callback
    """
    discount: str
    to_period: Optional[int] = None
    period: Optional[int] = None
    price: Optional[int] = None


class Category(CallbackData, prefix='category'):
    """
    [USER] Category callback
    """
    current_id: Optional[str] = None
    parent_id: Optional[str] = None


class CategoryCreate(CallbackData, prefix='category_create'):
    """
    [ADMIN] Category create callback
    """
    parent_id: Optional[str] = None


class CategoryRename(CallbackData, prefix='category_rename'):
    """
    [ADMIN] Category rename callback
    """
    current_id: Optional[str] = None
    parent_id: Optional[str] = None


class CategoryDelete(CallbackData, prefix='category_delete'):
    """
    [ADMIN] Category delete callback
    """
    current_id: Optional[str] = None
    parent_id: Optional[str] = None


class CategoryContent(CallbackData, prefix='category_content'):
    """
    [ADMIN] Category content callback
    """
    current_id: Optional[str] = None
    parent_id: Optional[str] = None


class CategoryClean(CallbackData, prefix='category_clean'):
    """
    [ADMIN] Category content clean
    """
    current_id: Optional[str] = None
    parent_id: Optional[str] = None


class CategoryCleanFinish(CallbackData, prefix='category_clean_finish'):
    """
    [ADMIN] Category content clean
    """
    current_id: Optional[str] = None
    parent_id: Optional[str] = None
    type: Optional[str] = None


class Mailing(CallbackData, prefix='mailing'):
    """
    [Admin] Mailing callback
    """


class SendMailing(CallbackData, prefix='send_mailing'):
    """
    [Admin] Mailing send
    """
    mes_id: int


class CategoryBack(CallbackData, prefix='category_back'):
    """
    [ADMIN] Category content clean
    """
    current_id: Optional[str] = None
