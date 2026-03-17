from typing import Unpack

from aiogram.types import BotCommand

from .._bot import BasicBot, BaseBotConfig
from .._tools import AiogramProxy
from .._alert import alert_wraps
from ...core.service import PDFService, FindService
from ...core.manager import MangaManager, AlertManager
from ...core import config


class UserBotConfig(BaseBotConfig):
    """Конфигурация для инициализации бота.

    Args:
        save_path (str | None, optional): Путь для хранение PDF - файлов
        token (str | None, optional): Токен Telegram-бота. По умолчанию берётся из конфига.
    """

    save_path: str | None
    token: str | None


class UserBot(BasicBot[UserBotConfig]):
    def __init__(
        self,
        manager: MangaManager,
        pdf_service: PDFService,
        find_service: FindService,
        alert: AlertManager,
        **config: Unpack[UserBotConfig],
    ) -> None:
        self.manager = manager
        self.pdf_service = pdf_service
        self._alert = alert
        self.find_service = find_service
        super().__init__(**config)

    @alert_wraps(
        "Пользовательская часть бота успешно запущена!",
        "Пользовательская часть бота прекратила свою работу",
    )
    async def run(self):
        await self.dispatcher.start_polling(self.bot)

    @property
    def token(self):
        return config.user_bot.api_key

    @property
    def proxy(self):
        return (
            AiogramProxy.create(config.user_bot.proxy)
            if config.user_bot.proxy
            else None
        )

    @property
    def alert(self):
        return self._alert

    @property
    def commands(self):
        return [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="download", description="Скачивает мангу по SKU"),
            BotCommand(command="find", description="Поиск манги по названию"),
            BotCommand(command="get_manga", description="Получить мангу по SKU"),
            BotCommand(command="/cancel", description="Отмена действие")
        ]
