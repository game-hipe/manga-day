import asyncio

import aiohttp

from sqlalchemy.ext.asyncio import create_async_engine
from loguru import logger

from src.core import config
from src.core.entities.schemas import ProxySchema
from src.core.entities.models import Base
from src.core.manager import MangaManager, SpiderManager, AlertManager

from src.frontend import start_frontend
from src.api import start_api
from src.bot import start_bot
from src.bot import start_user

from src.core import SpiderScheduler

from src.core.service import PDFService
from src.core.service import FindService


async def main():
    async with aiohttp.ClientSession() as session:
        engine = create_async_engine(config.database.db)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        alert = AlertManager()
        api = MangaManager(engine)

        proxy = [ProxySchema.create(x) for x in config.proxy]
        spider = SpiderManager(session, api, alert, "lxml", proxy=proxy)
        scheduler = SpiderScheduler(spider)

        find = FindService(api)
        pdf = PDFService(session, proxy=proxy)

        try:
            await asyncio.gather(
                start_bot(spider=spider),
                start_api(manager=api),
                start_frontend(manager=api, find=find, spider=spider),
                start_user(
                    manager=api,
                    alert=alert,
                    pdf_service=pdf,
                    save_path=config.pdf.save_path,
                ),
                scheduler.start(),
            )
        finally:
            await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем.")

    except Exception as e:
        logger.critical(f"Произошла ошибка: {e}")
        raise
