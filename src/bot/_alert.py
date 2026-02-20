import asyncio

from typing import Protocol
from functools import wraps

from aiogram import Bot
from aiogram.exceptions import TelegramNotFound
from loguru import logger

from ..core.manager import AlertManager
from ..core.abstract.alert import BaseAlert, LEVEL
from ..core import config


class HasAlertManager(Protocol):
    @property
    def alert(self) -> AlertManager | None: ...


class BotAlert(BaseAlert):
    """Логика уведомлений бота"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def alert(self, message: str, level: LEVEL):
        """Отправляет сообщение в чаты администраторов бота"""
        message += f"\n\nУровень: <b>{level}</b>"

        async def send(chat_id: int):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                )
            except TelegramNotFound:
                logger.warning(f"Чат {chat_id} не найден")

        await asyncio.gather(
            *[asyncio.create_task(send(chat_id)) for chat_id in config.bot.admins],
            return_exceptions=True,
        )

        return True


def alert_wraps(on_start: str, on_stop: str):
    def wrapper(func):
        @wraps(func)
        async def inner(self: HasAlertManager, *args, **kwargs):
            if self.alert:
                logger.warning(on_start)
                await self.alert.alert(on_start, "info")
            try:
                return await func(self, *args, **kwargs)
            finally:
                if self.alert:
                    logger.warning(on_stop)
                    await self.alert.alert(on_stop, "warning")

        return inner

    return wrapper
