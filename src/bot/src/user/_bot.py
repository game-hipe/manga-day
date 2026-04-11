from typing import Unpack

from aiogram.types import BotCommand

from .._bot import BasicBot, BaseBotConfig
from .._alert import alert_wraps
from ..core.pdf import PDFmanager
from ..core.api import API
from ..core.alert import AlertManager


class UserBotConfig(BaseBotConfig):
    site: str | None = None
    """Сайт на котором можно смотреть мангу"""


class UserBot(BasicBot[UserBotConfig]):
    def __init__(
        self,
        api: API,
        pdf: PDFmanager,
        alert: AlertManager,
        **config: Unpack[UserBotConfig],
    ) -> None:
        self.api = api
        self.pdf = pdf
        self._alert = alert
        super().__init__(**config)

    @alert_wraps(
        "Пользовательская часть бота успешно запущена!",
        "Пользовательская часть бота прекратила свою работу",
    )
    async def run(self):
        await self.dispatcher.start_polling(self.bot)

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
            BotCommand(command="get", description="Получить мангу по SKU"),
            BotCommand(command="cancel", description="Отмена действие"),
            BotCommand(command="random", description="Получить рандомную мангу"),
        ]
