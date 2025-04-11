"""User routers connect"""
__all__ = ("router", )
from aiogram import Router
from .message import router as router_message
from .callback import router as router_callback


router = Router()
router.include_routers(router_message, router_callback)
