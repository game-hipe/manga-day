from typing import Unpack

from aiogram.types import BotCommand

from .middleware.admins import AdminMiddleware
from .._bot import BasicBot, BaseBotConfig
from .._alert import BotAlert, alert_wraps
from ..core.api import AdminAPI
from ..core.alert import AlertManager


class AdminBotConfig(BaseBotConfig):
    admin_ids: list[int]


class AdminBot(BasicBot[AdminBotConfig]):
    def __init__(
        self,
        api: AdminAPI,
        alert: AlertManager,
        **config: Unpack[AdminBotConfig],
    ) -> None:
        self.api = api
        self._alert = alert
        super().__init__(**config)
        if self.alert:
            self.alert.add_alert(BotAlert(self.bot, self.config.get("admin_ids")))

    @alert_wraps(
        "Административная часть бота успешно запущена!",
        "Административная часть бота прекратила свою работу",
    )
    async def run(self):
        bot = self.bot
        dispatcher = self.dispatcher

        dispatcher.message.middleware(AdminMiddleware(self.config.get("admin_ids")))

        await dispatcher.start_polling(bot)

    @property
    def alert(self):
        return self._alert

    @property
    def commands(self):
        return [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="download", description="Скачивает мангу по SKU"),
            BotCommand(command="start_parsing", description="Запустить парсинг"),
            BotCommand(command="stop_parsing", description="Остановить парсинг"),
            BotCommand(
                command="stop_spider", description="Остановить парсинг выбранного паука"
            ),
            BotCommand(
                command="start_spider", description="Запустить парсинг выбранного паука"
            ),
            BotCommand(command="status", description="Статус парсинга"),
        ]
