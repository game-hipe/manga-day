import asyncio

import aiohttp

from sqlalchemy.ext.asyncio import create_async_engine
from loguru import logger

from src.core import config
from src.core.entites.models import Base
from src.core.manager.manga import MangaManager
from src.spider import HmangaSpider, MultiMangaSpider
from src.core.abstract.spider import BaseSpider

URL = "https://api.telegram.org/bot{token}/sendMessage".format(token=config.bot.api_key)


async def send_message(message: str, session: aiohttp.ClientSession):
    async def send(message: str, chat_id: int):
        async with session.get(
            URL, data={"chat_id": chat_id, "text": message}
        ) as response:
            await response.text()

    tasks = []
    for chat_id in config.bot.admins:
        tasks.append(asyncio.create_task(send(message, chat_id)))

    await asyncio.gather(*tasks)


async def start_parsing(
    spider_factory: type[BaseSpider],
    session: aiohttp.ClientSession,
    manager: MangaManager,
    features: str = None,
):
    try:
        spider = spider_factory(session, manager, features)
        await spider.run()

    except Exception as e:
        await send_message(
            f"Ошибка при запуске/работе парсера {spider_factory.__name__}: {e}"
        )
        logger.error(
            f"Ошибка при запуске/работе парсера {spider_factory.__name__}: {e}"
        )

    finally:
        await send_message(f"Парсер завершил работу {spider_factory.__name__}", session)


async def main():
    async with aiohttp.ClientSession() as session:
        engine = create_async_engine(config.database.db)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        api = MangaManager(engine)

        tasks = [
            asyncio.create_task(start_parsing(spider, session, api, "lxml"))
            for spider in [HmangaSpider, MultiMangaSpider]
        ]

        await asyncio.gather(*tasks)

        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем.")

    except Exception as e:
        logger.critical(f"Произошла ошибка: {e}")
