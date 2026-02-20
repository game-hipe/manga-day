from typing import Unpack

from aiogram.types import BotCommand

from .handler.commands import CommandsHandler
from .._bot import BasicBot, BaseBotConfig
from .._tools import AiogramProxy
from .._alert import alert_wraps
from ...core.service import PDFService
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
        alert: AlertManager,
        **config: Unpack[UserBotConfig],
    ) -> None:
        self.manager = manager
        self.pdf_service = pdf_service
        self._alert = alert
        super().__init__(**config)

    @alert_wraps(
        "Пользовательская часть бота успешно запущена!",
        "Пользовательская часть бота прекратила свою работу",
    )
    async def run(self):
        bot = self.bot
        dispatcher = self.dispatcher
        handler = CommandsHandler(
            self.manager, self.pdf_service, self.config.get("save_path")
        )

        dispatcher.include_router(handler.router)
        await dispatcher.start_polling(bot)

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
        ]


async def setup_user(
    manager: MangaManager,
    pdf_service: PDFService,
    alert: AlertManager,
    **config: Unpack[UserBotConfig],
) -> UserBot:
    """Инцилизация клиентской части бота

    Args:
        manager (MangaManager): Менеджнр манги.
        pdf_service (PDFService): Сервис для генерации PDF
        alert (AlertManager): Система алёртов.

    Returns:
        UserBot: Класс для управление ботом.
    """
    bot = UserBot(manager, pdf_service, alert, **config)
    await bot.set_command()
    return bot


async def start_user(
    manager: MangaManager,
    pdf_service: PDFService,
    alert: AlertManager,
    **config: Unpack[UserBotConfig],
):
    """Инцилизация клиентской части бота, и дальнейший её запуск

    Args:
        manager (MangaManager): Менеджнр манги.
        pdf_service (PDFService): Сервис для генерации PDF
        alert (AlertManager): Система алёртов.
    """
    try:
        bot = await setup_user(manager, pdf_service, alert, **config)
        await bot.run()
    finally:
        await bot.bot.session.close()
