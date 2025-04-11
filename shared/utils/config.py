"""ENV SETTINGS"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings class
    """
    BOT_TOKEN: str

    MONGO_USERNAME: str
    MONGO_PASSWORD: str
    MONGO_HOST: str
    MONGO_HOST_EXTERNAL: str
    MONGO_PORT: int
    MONGO_PORT_EXTERNAL: int
    MONGO_DB_NAME: str
    MONGO_DB_ROOT_NAME: str

    ADMIN_IDS: List[int]
    CACHE_CHAT_ID: int

    ROBOKASSA_LOGIN: str
    ROBOKASSA_PASSWORD_1: str
    ROBOKASSA_PASSWORD_2: str

    model_config = SettingsConfigDict(env_file="/app/.env")


settings = Settings()
