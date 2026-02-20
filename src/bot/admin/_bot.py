from typing import Unpack

from aiogram.types import BotCommand

from .handler.commands import CommandsHandler
from .middleware.admins import AdminMiddleware
from .._bot import BasicBot, BaseBotConfig
from .._tools import AiogramProxy, get_router
from .._alert import BotAlert, alert_wraps
from ...core.manager import SpiderManager
from ...core import config


class AdminBotConfig(BaseBotConfig):
    admin_ids: list[int] | None = None


class AdminBot(BasicBot[AdminBotConfig]):
    def __init__(
        self,
        spider: SpiderManager,
        **config: Unpack[AdminBotConfig],
    ) -> None:
        self.spider = spider
        super().__init__(**config)
        if self.alert:
            self.alert.add_alert(BotAlert(self.bot))

    @alert_wraps(
        "Административная часть бота успешно запущена!",
        "Административная часть бота прекратила свою работу",
    )
    async def run(self):
        bot = self.bot
        dispatcher = self.dispatcher
        handler = CommandsHandler(self.spider)

        dispatcher.include_router(handler.router)
        dispatcher.include_router(get_router())
        dispatcher.message.middleware(
            AdminMiddleware(self.config.get("admin_ids") or config.bot.admins)
        )

        await dispatcher.start_polling(bot)

    @property
    def token(self):
        return config.bot.api_key

    @property
    def proxy(self):
        return AiogramProxy.create(config.bot.proxy) if config.bot.proxy else None

    @property
    def alert(self):
        return self.spider.alert

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


async def setup_admin(
    spider: SpiderManager, **config: Unpack[BaseBotConfig]
) -> AdminBot:
    """Инцилизация админки возращает экземпляр класса AdminBot

    Args:
        spider (SpiderManager): Менеджер пауков.

    Returns:
        AdminBot: Админка бота.
    """
    bot = AdminBot(spider, **config)
    await bot.set_command()
    return bot


async def start_admin(spider: SpiderManager, **config: Unpack[BaseBotConfig]) -> None:
    """Инцилизация админки, и дальнейший запуск.

    Args:
        spider (SpiderManager): Менеджер пауков.
    """
    try:
        bot = await setup_admin(spider, **config)
        await bot.run()
    finally:
        await bot.bot.session.close()
