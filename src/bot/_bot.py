from typing import TypedDict, Unpack

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage

from ..core import config
from ..core.manager.spider import SpiderManager
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
            BotCommand(command="status", description="Статус парсинга"),
        ]
    )


async def setup_bot(**kwargs: Unpack[BotConfig]) -> tuple[Bot, Dispatcher]:
    spider = kwargs.get("spider")
    token = kwargs.get("token") or config.bot.api_key

    if spider is None:
        raise AttributeError("SpiderManager не указан")
    elif not isinstance(spider, SpiderManager):
        raise TypeError("SpiderManager должен быть экземпляром SpiderManager")

    bot = Bot(token=token)
    storage = MemoryStorage()

    spider.add_alert(BotAlert(bot))

    await set_command(bot)
    dp = Dispatcher(storage=storage)

    return bot, dp


async def start_bot(**kwargs: Unpack[BotConfig]):
    bot, dp = await setup_bot(**kwargs)

    await dp.start_polling(bot)
