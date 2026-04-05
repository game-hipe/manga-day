import asyncio

from typing import Protocol, Literal
from functools import wraps

from aiogram import Bot
from aiogram.exceptions import TelegramNotFound
from loguru import logger

from .core.alert import AlertManager
from .core.abstract.alert import BaseAlert, LEVEL


class HasAlertManager(Protocol):
    @property
    def alert(self) -> AlertManager | None: ...


class BotAlert(BaseAlert):
    """Логика уведомлений бота"""

    def __init__(self, bot: Bot, admin_ids: list[int]):
        self.bot = bot
        self._admin_ids = admin_ids

        if not self._admin_ids:
            raise ValueError("Не указаны администраторы бота")

    async def alert(self, message: str, level: LEVEL) -> Literal[True]:
        """Отправляет сообщение в чаты администраторов бота

        Args:
            message (str): Сообщение которое будет отправлено администраторам
            level (LEVEL): Уровень сообщения

        Returns:
            Literal[True]: Всегда возвращает True
        """
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
            *[asyncio.create_task(send(chat_id)) for chat_id in self.admin_ids],
            return_exceptions=True,
        )

        return True

    @property
    def admin_ids(self):
        return self._admin_ids.copy()


def alert_wraps(on_start: str, on_stop: str):
    """Декоратор, что-бы в конце функции вывести уведомить.

    Args:
        on_start (str): Сообщение, которое будет отправлено при начале выполнения функции
        on_stop (str): Сообщение, которое будет отправлено при завершении выполнения функции
    """

    def wrapper(func):
        @wraps(func)
        async def inner(self: HasAlertManager, *args, **kwargs):
            logger.info(on_start)
            if self.alert:
                await self.alert.alert(on_start, "info")
            try:
                return await func(self, *args, **kwargs)
            finally:
                logger.warning(on_stop)
                if self.alert:
                    await self.alert.alert(on_stop, "warning")

        return inner

    return wrapper
