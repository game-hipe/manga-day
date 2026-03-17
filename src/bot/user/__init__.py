from typing import Unpack

from loguru import logger

from ...core import service, manager
from ._bot import UserBotConfig, UserBot
from .handler import StartHandler, FindCommandsHandler, GetMangaCommandHandler

__all__ = ["setup_user", "start_user", "UserBotConfig", "UserBot"]


async def setup_user(
    manager: manager.MangaManager,
    pdf_service: service.PDFService,
    find_service: service.FindService,
    alert: manager.AlertManager,
    **config: Unpack[UserBotConfig],
) -> UserBot:
    """Инициализация клиентской части бота

    Args:
        manager (MangaManager): Менеджер манги.
        pdf_service (PDFService): Сервис для генерации PDF
        find_service (FindService): Сервис для поиска манги
        alert (AlertManager): Система уведомлений.

    Returns:
        UserBot: Класс для управление ботом.
    """
    bot = UserBot(manager, pdf_service, find_service, alert, **config)

    logger.debug("Бот инцилизирован")
    await bot.set_command()
    logger.debug("Команды установлены")

    bot.include_router(StartHandler(bot))
    bot.include_router(FindCommandsHandler(bot))
    bot.include_router(GetMangaCommandHandler(bot))

    return bot


async def start_user(
    manager: manager.MangaManager,
    pdf_service: service.PDFService,
    find_service: service.FindService,
    alert: manager.AlertManager,
    **config: Unpack[UserBotConfig],
):
    """Инициализация клиентской части бота, и дальнейший её запуск

    Args:
        manager (MangaManager): Менеджер манги.
        pdf_service (PDFService): Сервис для генерации PDF
        find_service (FindService): Сервис для поиска манги
        alert (AlertManager): Система уведомлений.
    """
    bot = None
    try:
        bot = await setup_user(manager, pdf_service, find_service, alert, **config)
        await bot.run()
    finally:
        if bot is not None:
            await bot.bot.session.close()
            logger.debug("Сессия закрыта")

        else:
            logger.warning("Инициализация не удалась (bot='UserBot')")
