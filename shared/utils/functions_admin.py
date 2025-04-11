"""Functions for admin panel"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from shared.utils.callbacks import Category, Knowledge


async def keyboard_back(parent_id, locale) -> InlineKeyboardMarkup:
    """
    Create back button in Admin panel
    :param parent_id:
    :param locale:
    :return: keyboard button
    """
    keyboard = InlineKeyboardBuilder()
    if parent_id:
        keyboard.row(InlineKeyboardButton(text=locale.backbutton(),
                                          callback_data=Category(
                                              current_id=parent_id).pack()))
    else:
        keyboard.row(InlineKeyboardButton(text=locale.backbutton(),
                                          callback_data=Knowledge().pack()))
    return keyboard.as_markup()




def back_category(locale, current_id, parent_id) -> InlineKeyboardBuilder:
    """
    Back button after uploading
    :param locale:
    :param current_id:
    :param parent_id:
    :return:
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text=locale.backbutton(),
        callback_data=Category(current_id=current_id, parent_id=parent_id).pack()))
    return keyboard
