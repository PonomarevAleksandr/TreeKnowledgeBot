"""Bot middlewares"""
import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Union
from fluentogram import TranslatorHub
from aiogram.exceptions import TelegramBadRequest
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from cachetools import TTLCache
from motor.motor_asyncio import AsyncIOMotorClient

from shared.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

caches = {
    "default": TTLCache(maxsize=10_000, ttl=0.1)
}


class TranslateMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """
    Fluentogram translation middleware
    """

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        language = data['user'].language_code if 'user' in data else 'ru'

        hub: TranslatorHub = data.get('t_hub')

        data['locale'] = hub.get_translator_by_locale(language)

        return await handler(event, data)


class UserMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """
    Automatic user insert to db
    """

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        if not hasattr(event, "from_user") or event.from_user is None:
            return await handler(event, data)

        user = await data["db"].users.find_one(f={"id": event.from_user.id})

        if isinstance(event, Message):
            if user is None:
                new_user = event.from_user.model_dump()
                new_user["created_at"] = int(time.time())
                new_user["updated_at"] = int(time.time())

                if event.text and "rl" in event.text:
                    try:
                        new_user["refer_id"] = int(event.text.replace("rl", ""))
                    except ValueError:
                        pass

                user = User(**new_user)
                await data["db"].users.insert_one(user.model_dump())
            elif user.blocked_at is not None:
                await data["db"].users.update_one(
                    {"chat_id": event.from_user.id}, {"$set": {"blocked_at": None}}
                )

            if user.updated_at < time.time() - 300:
                await data["db"].users.update_one(
                    {"chat_id": event.from_user.id},
                    {"$set": event.from_user.model_dump()},
                )

        data["user"] = user
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """
    Throttling middleware
    """

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        if not hasattr(event, "from_user") or event.from_user is None:
            return await handler(event, data)

        if event.from_user.id in caches["default"]:
            return
        caches["default"][event.from_user.id] = None
        return await handler(event, data)


class DataBaseMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """
    Data base middleware
    """

    def __init__(self, db: AsyncIOMotorClient):
        super().__init__()
        self.db = db

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        return await handler(event, data)


class AlbumMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """
    Album middleware
    """
    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        self.latency = latency

    async def __call__(
            self,
            handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
            message: Message,
            data: dict[str, Any]
    ) -> Any:
        if not message.media_group_id:
            await handler(message, data)
            return
        try:
            self.album_data[message.media_group_id].append(message)
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            data['_is_last'] = True
            data["album"] = self.album_data[message.media_group_id]
            await handler(message, data)

        if message.media_group_id and data.get("_is_last"):
            del self.album_data[message.media_group_id]
            del data['_is_last']


class MessageCleanupMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """
    Message cleanup middleware
    """

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Union[Message, CallbackQuery],
            data: Dict[str, Any]
    ) -> Any:
        bot = data['bot']
        db = data['db']

        user = await db.users.find_one({"id": event.from_user.id})
        try:
            if user.message_ids:
                for message_id in user.message_ids:
                    try:
                        await bot.delete_message(
                            chat_id=event.from_user.id,
                            message_id=message_id
                        )
                    except TelegramBadRequest:
                        continue
        except TelegramBadRequest:
            await db.users.update_one(
                {"id": event.from_user.id},
                {"message_ids": []}
            )
        return await handler(event, data)
