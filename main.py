import asyncio

import aiohttp

from sqlalchemy.ext.asyncio import create_async_engine
from loguru import logger

from src.core import config
from src.core.entites.models import Base
from src.core.manager.manga import MangaManager
from src.core.manager.spider import SpiderManager
from src.bot import start_bot
from src.core import SpiderScheduler


async def main():
    async with aiohttp.ClientSession() as session:
        engine = create_async_engine(config.database.db)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        api = MangaManager(engine)
        spider = SpiderManager(session, api, "lxml")
        scheduler = SpiderScheduler(spider)

        await asyncio.gather(start_bot(spider=spider), scheduler.start())
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем.")

    # except Exception as e:
    #    logger.critical(f"Произошла ошибка: {e}")
