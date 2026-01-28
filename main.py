import asyncio

import aiohttp

from aiogram import Bot
from sqlalchemy.ext.asyncio import create_async_engine
from loguru import logger

from src.core import config
from src.core.entites.models import Base
from src.core.manager.manga import MangaManager
from src.core.manager.spider import SpiderManager
from src.bot._alert import BotAlert


async def main():
    async with aiohttp.ClientSession() as session:
        engine = create_async_engine(config.database.db)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        api = MangaManager(engine)

        async with Bot(config.bot.api_key) as bot:
            spider = SpiderManager(session, api, "lxml")
            spider.add_alert(BotAlert(bot))

            await spider.start_parsing()

        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем.")

    # except Exception as e:
    #    logger.critical(f"Произошла ошибка: {e}")
