from typing import Unpack

from loguru import logger

from .handler import CommandsHandler
from .._tools import cancel_router, get_router
from ..core.api import AdminAPI
from ..core.alert import AlertManager
from ._bot import AdminBotConfig, AdminBot

__all__ = [
    "setup_admin",
    "start_admin",
    "AdminBotConfig",
]


async def setup_admin(
    api: AdminAPI, alert: AlertManager, **config: Unpack[AdminBotConfig]
) -> AdminBot:
    """Инициализация админки возвращает экземпляр класса AdminBot

    Args:
        api (AdminAPI): API для работы с БД

    Returns:
        AdminBot: Админка бота.
    """
    bot = AdminBot(api, alert, **config)
    bot.include_router(cancel_router())
    bot.include_router(CommandsHandler(bot))
    bot.include_router(get_router())

    await bot.set_command()
    return bot


async def start_admin(
    api: AdminAPI, alert: AlertManager, **config: Unpack[AdminBotConfig]
) -> None:
    """Инициализация админки, и дальнейший запуск.

    Args:
        api (AdminAPI): API для работы с БД
    """
    bot = None
    try:
        bot = await setup_admin(api, alert, **config)
        await bot.run()
    finally:
        if bot is not None:
            await bot.bot.session.close()
            await bot.bot.session.close()
            logger.debug("Сессия закрыта")

        else:
            logger.warning("Инициализация не удалась (bot='AdminBot')")
