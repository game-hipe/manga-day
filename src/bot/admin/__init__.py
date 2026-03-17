from typing import Unpack

from loguru import logger

from .handler import CommandsHandler
from .._tools import get_router
from ...core.manager import SpiderManager
from ._bot import AdminBotConfig, AdminBot

__all__ = [
    "setup_admin",
    "start_admin",
    "AdminBotConfig",
]


async def setup_admin(
    spider: SpiderManager, **config: Unpack[AdminBotConfig]
) -> AdminBot:
    """Инициализация админки возвращает экземпляр класса AdminBot

    Args:
        spider (SpiderManager): Менеджер пауков.

    Returns:
        AdminBot: Админка бота.
    """
    bot = AdminBot(spider, **config)

    bot.include_router(CommandsHandler(bot))
    bot.include_router(get_router())

    await bot.set_command()
    return bot


async def start_admin(spider: SpiderManager, **config: Unpack[AdminBotConfig]) -> None:
    """Инициализация админки, и дальнейший запуск.

    Args:
        spider (SpiderManager): Менеджер пауков.
    """
    bot = None
    try:
        bot = await setup_admin(spider, **config)
        await bot.run()
    finally:
        if bot is not None:
            await bot.bot.session.close()
            await bot.bot.session.close()
            logger.debug("Сессия закрыта")

        else:
            logger.warning("Инициализация не удалась (bot='UserBot')")
