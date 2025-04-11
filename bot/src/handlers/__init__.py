"""Connect All Routers to main.py """
__all__ = ("router", )
from aiogram import Router
from .user import router as user_router
from .admin import router as admin_router



router = Router()
router.include_routers(user_router, admin_router)
