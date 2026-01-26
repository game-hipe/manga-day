import asyncio

import aiohttp

from sqlalchemy.ext.asyncio import create_async_engine

from src.core.entites.models import Base
from src.core import config
from src.core.manager.manga import MangaManager
from src.spider import HmangaSpider, MultiMangaSpider

async def main():
    async with aiohttp.ClientSession() as session:
        engine = create_async_engine(config.database.db)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        api = MangaManager(engine)
        h_spider = HmangaSpider(session, api, 'lxml')
        m_spider = MultiMangaSpider(session, api, 'lxml')
        
        await asyncio.gather(
            h_spider.run(),
            m_spider.run()
        )
        
        await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())