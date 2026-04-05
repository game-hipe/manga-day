from typing import Unpack

from loguru import logger

from ..core.api import API
from ..core.pdf import PDFmanager
from ..core.alert import AlertManager
from ._bot import UserBotConfig, UserBot
from .handler import StartHandler, FindCommandsHandler, GetMangaCommandHandler
from .._tools import get_router, cancel_router

__all__ = ["setup_user", "start_user", "UserBotConfig", "UserBot"]


async def setup_user(
    api: API,
    pdf: PDFmanager,
    alert: AlertManager,
    **config: Unpack[UserBotConfig],
) -> UserBot:
    """Инициализация клиентской части бота

    Args:
        api (API): API для работы с БД
        pdf (PDFmanager): Менеджер для генерации PDF
        alert (AlertManager): Система уведомлений.

    Returns:
        UserBot: Класс для управление ботом.
    """
    bot = UserBot(api, pdf, alert, **config)

    logger.debug("Бот инцилизирован")
    await bot.set_command()
    logger.debug("Команды установлены")
    bot.include_router(cancel_router())
    bot.include_router(StartHandler(bot))
    bot.include_router(GetMangaCommandHandler(bot))
    bot.include_router(FindCommandsHandler(bot))
    bot.include_router(get_router())

    return bot


async def start_user(
    api: API,
    pdf: PDFmanager,
    alert: AlertManager,
    **config: Unpack[UserBotConfig],
):
    """Инициализация клиентской части бота

    Args:
        api (API): API для работы с БД
        pdf (PDFmanager): Менеджер для генерации PDF
        alert (AlertManager): Система уведомлений.

    Returns:
        UserBot: Класс для управление ботом.
    """
    bot = None
    try:
        bot = await setup_user(api, pdf, alert, **config)
        await bot.run()
    finally:
        if bot is not None:
            await bot.bot.session.close()
            logger.debug("Сессия закрыта")

        else:
            logger.warning("Инициализация не удалась (bot='UserBot')")
