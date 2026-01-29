import asyncio

from itertools import batched
from typing import Awaitable, Optional

from loguru import logger

from ...core.abstract.spider import BaseSpider
from .parser import GlobalMangaParser, GlobalPageParser


class BaseMangaSpider(BaseSpider):
    PAGE_URL = "/page/{page}/"
    
    MANGA_PARSER: type[GlobalMangaParser]
    PAGE_PARSER: type[GlobalPageParser]
    
    async def get(self, url):
        parser = self.MANGA_PARSER(self.BASE_URL, self.features)

        markup = await self.http.get(url, "read")
        if markup is None:
            logger.error(f"Не удалось получить страницу: {url}")
            return

        return parser.parse(markup)

    async def pages(self, start_page: int | None = None):
        parser = self.PAGE_PARSER(self.BASE_URL, self.features)

        markup = await self.http.get(self.BASE_URL, "read")

        if markup is None:
            logger.error(f"Не удалось получить страницу: {self.BASE_URL}")
            return

        soup = parser.build_soup(markup)
        max_page = max(
            [
                int(page.get_text(strip=True))
                for page in soup.select("section.pagination a")
                if page.get_text(strip=True).isdigit()
            ]
        )

        for url_batch in batched(
            map(
                lambda x: parser.urljoin(self.PAGE_URL.format(page=x)),
                range(start_page or 2, max_page + 1),
            ),
            self.batch,
        ):
            tasks: list[Awaitable[Optional[bytes]]] = []
            for url in url_batch:
                tasks.append(asyncio.create_task(self.http.get(url, "read")))

            for task in asyncio.as_completed(tasks):
                response = await task
                if response is None:
                    continue

                yield parser.parse(response)
