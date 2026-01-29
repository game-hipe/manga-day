from typing import TypedDict, Unpack
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from ..core import config
from ..core.manager.spider import SpiderManager
from .handlers.commands import CommandsHandler
from .middleware.admins import AdminMiddleware
from ._alert import BotAlert

class BotConfig(TypedDict):
    spider: SpiderManager
    token: str | None = None


async def set_command(bot: Bot):
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="startparsing", description="Запустить парсинг"),
            BotCommand(command="stopparsing", description="Остановить парсинг"),
            BotCommand(command="status", description="Статус парсинга"),
        ]
    )


@asynccontextmanager
async def setup_bot(**kwargs: Unpack[BotConfig]):
    spider = kwargs.get("spider")
    token = kwargs.get("token") or config.bot.api_key

    if spider is None:
        raise AttributeError("SpiderManager не указан")
    elif not isinstance(spider, SpiderManager):
        raise TypeError("SpiderManager должен быть экземпляром SpiderManager")

    dp = None
    try:
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        async with Bot(
            token=token, default=DefaultBotProperties(parse_mode="HTML")
        ) as bot:
            logger.info("Инцилизация бота...")
            await set_command(bot)

            spider.add_alert(BotAlert(bot))
            handler = CommandsHandler(spider_manager=spider)

            dp.include_routers(handler.router)
            dp.message.middleware(AdminMiddleware(config.bot.admins))
            
            logger.info("Бот ицилизирован")
            yield bot, dp
    finally:
        if dp is not None:
            try:
                await dp.stop_polling()
            except RuntimeError:
                ...
        await spider.alert("<b>Бот прекратил свою работу</b>")
        logger.info("Бот остановлен")


async def start_bot(**kwargs: Unpack[BotConfig]):
    async with setup_bot(**kwargs) as (bot, dp):
        logger.success("Бот запущен")
        await dp.start_polling(bot)
