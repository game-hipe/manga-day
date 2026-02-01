import asyncio

from typing import Optional, AsyncGenerator
from itertools import batched

from bs4 import BeautifulSoup
from loguru import logger
from pydantic import HttpUrl

from ...core.entities.schemas import BaseManga
from ...core.abstract.spider import BaseSpider
from .parser import HitomiMangaParser, HitomiPageParser


class HitomiSpider(BaseSpider):
    BASE_URL = "https://hitomi.si"
    CUSTOM_COOKIES = {
        "read": "1",
    }

    PAGE_URL = "/latest?page={page}"
    """URL - для того что-бы получить максимальное число страниц"""

    MANGA = "/spa/manga/{id}/read"
    """URL - для получение галлереи"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._total_pages: Optional[int] = None
        self._processed_pages: int = 0
        self._max_page_fetched: bool = False

    @property
    async def total_pages(self) -> int:
        if self._max_page_fetched:
            return self.total_pages

        response = await self.http.get(
            self.urljoin(
                self.PAGE_URL.format(page=99999)
            ),  # Число 99999 так-как при огромном количестве страниц сайт по просту возращает последнюю страницу
            "read",
            cookies=self.CUSTOM_COOKIES,
        )

        if response is None:
            logger.error(
                f"Не удалось получить начальную страницу для определения пагинации: {self.BASE_URL}"
            )
            self._total_pages = 1
            self._max_page_fetched = True
            return self._total_pages
        else:
            logger.debug(
                f"Получена начальная страница для определения пагинации: {self.BASE_URL}"
            )
            soup = BeautifulSoup(response, self.features)
            page_links = [
                x
                for x in soup.select("div.pagination a")
                if x.get_text(strip=True).isdigit()
            ]
            try:
                self._total_pages = max(
                    int(page.get_text(strip=True))
                    for page in page_links
                    if page.get_text(strip=True).isdigit()
                )
            except ValueError:
                logger.warning(
                    "Не удалось определить максимальную страницу. Установлено: 1"
                )
                self._total_pages = 1
            self._max_page_fetched = True
            logger.debug(
                f"Определено максимальное количество страниц: {self._total_pages}"
            )

            return self._total_pages or 1

    async def get(self, url):
        parser = HitomiMangaParser(self.BASE_URL, self.features)

        markup = await self.http.get(url, "read")
        if markup is None:
            logger.error(f"Не удалось получить страницу: {url}")
            return

        base_manga = parser.parse(markup, features=self.features, situation="html")

        id = url.split("/")[-1].replace("si", "")
        gallery = await self.http.get(self.urljoin(self.MANGA.format(id=id)), "json")
        if gallery is None:
            logger.error(f"Не удалось получить галлерею: {url}")
            return

        base_manga.gallery.extend(
            [HttpUrl(x) for x in parser.parse(gallery, situation="json")]
        )

        return base_manga

    @property
    def status(self) -> str:
        """
        Возвращает текущий статус прогресса парсинга в процентах.

        Returns:
            str: Процент выполнения в формате "XX%". Например: "67%"
        """
        total = self._total_pages or 1
        percent = (self._processed_pages / total) * 100
        return f"{int(percent)}%"

    async def pages(
        self, start_page: int | None = None
    ) -> AsyncGenerator[BaseManga, None]:
        parser = HitomiPageParser(self.BASE_URL, self.features)

        total = await self.total_pages
        logger.info(f"Обнаружено всего страниц: {total}")

        start = start_page or 1
        if start > total:
            logger.info("Начальная страница больше максимальной. Парсинг завершён.")
            return

        for url_batch in batched(
            (
                self.urljoin(self.PAGE_URL.format(page=page))
                for page in range(start, total + 1)
            ),
            self.batch,
        ):
            tasks = [
                asyncio.create_task(self.http.get(url, "read")) for url in url_batch
            ]

            for task in asyncio.as_completed(tasks):
                response = await task
                if response is None:
                    continue

                self._processed_pages += 1  # Увеличиваем счётчик обработанных страниц
                logger.debug(
                    f"Обработана страница {self._processed_pages}/{total} ({self.status})"
                )

                soup = parser.build_soup(response)
                yield parser.parse(soup)
