"""Базовый Бот."""

from abc import ABC, abstractmethod
from typing import TypedDict, Unpack, TypeVar, Generic

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand
from loguru import logger

from ._tools import AiogramProxy
from ._alert import BotAlert
from ..core.manager import AlertManager


class BaseBotConfig(TypedDict):
    """Конфигурация для инициализации бота.

    Args:
        token (str | None, optional): Токен Telegram-бота. По умолчанию берётся из конфига.
    """

    token: str | None


_T = TypeVar("_T", bound=BaseBotConfig)


class BasicBot(ABC, Generic[_T]):
    """Базовый Бот."""

    def __init__(self, **config: Unpack[_T]) -> None:
        self.config: _T = config
        self._bot: Bot | None = None
        self._dispatcher: Dispatcher | None = None

        self.alert.add_alert(BotAlert(self.bot))

    async def run(self):
        """Запуск бота"""
        await self.set_command()

    async def set_command(self, bot: Bot | None = None) -> None:
        """Установить команды боту.

        Args:
            bot (Bot | None, optional): Экземпляр бота. По умолчанию берётся из self.bot.
        """
        bot = bot or self.bot
        if not self.commands:
            return

        await bot.set_my_commands(self.commands)

    @property
    @abstractmethod
    def token(self) -> str:
        """Токен бота."""

    @property
    def commands(self) -> list[BotCommand] | None:
        logger.warning("Команды не настроены")

    @property
    def proxy(self) -> AiogramProxy | None:
        """Прокси для бота."""
        logger.warning("Прокси не настроен")

    @property
    def alert(self) -> AlertManager | None:
        """Менеджер уведомлений."""
        logger.warning("Менеджер уведомлений не настроен")

    @property
    def bot(self) -> Bot:
        """Экземпляр бота."""
        if self._bot is None:
            self._bot = self._create_bot()
            return self._bot
        else:
            return self._bot

    @property
    def dispatcher(self) -> Dispatcher:
        """Экземпляр диспетчера."""
        if self._dispatcher is None:
            self._dispatcher = self._create_dispatcher()
            return self._dispatcher
        else:
            return self._dispatcher

    def _create_bot(self, token: str | None = None) -> Bot:
        """Создаёт бота.

        Args:
            token (str, optional): Токен Telegram-бота. По умолчанию берётся из конфига.

        Returns:
            Bot: Экземпляр бота.
        """
        logger.debug("Инцилизация бота бота.")
        session = AiohttpSession(proxy=self.proxy.auth() if self.proxy else None)

        return Bot(
            token=token or self.token,
            session=session,
            default=DefaultBotProperties(parse_mode="HTML"),
        )

    def _create_dispatcher(
        self, storage: BaseStorage | None = None, bot: Bot | None = None
    ) -> Dispatcher:
        """Возращает экземпляр диспетчера.

        Args:
            storage (BaseStorage | None, optional): Место где будут храниться все состоянии. Обычное состояние None.
            bot (Bot | None, optional): Экземпляр бота, если не указано, то создаётся новый. Обычное состояние None.

        Returns:
            Dispatcher: Экземпляр диспетчера.
        """
        logger.debug("Инцилизация диспетчера.")
        return Dispatcher(storage=storage or MemoryStorage(), bot=bot or self.bot)
