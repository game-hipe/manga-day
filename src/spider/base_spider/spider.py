import asyncio

from itertools import batched
from typing import AsyncGenerator, Optional

from loguru import logger

from ...core.abstract.spider import BaseSpider, BaseManga
from .parser import GlobalMangaParser, GlobalPageParser


class BaseMangaSpider(BaseSpider):
    PAGE_URL = "/page/{page}/"

    MANGA_PARSER: type[GlobalMangaParser]
    PAGE_PARSER: type[GlobalPageParser]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._total_pages: Optional[int] = None
        self._processed_pages: int = 0
        self._max_page_fetched: bool = False

    async def get(self, url):
        parser = self.MANGA_PARSER(self.BASE_URL, self.features)

        markup = await self.http.get(url, "read")
        if markup is None:
            logger.error(f"Не удалось получить страницу: {url}")
            return

        return parser.parse(markup)

    @property
    async def total_pages(self) -> int:
        """Асинхронно вычисляет и кэширует общее количество страниц."""
        if self._total_pages is None and not self._max_page_fetched:
            parser = self.PAGE_PARSER(self.BASE_URL, self.features)
            markup = await self.http.get(self.BASE_URL, "read")

            if markup is None:
                logger.error(
                    f"Не удалось получить начальную страницу для определения пагинации: {self.BASE_URL}"
                )
                self._total_pages = 1  # Защита от крайних случаев
                self._max_page_fetched = True
                return self._total_pages

            soup = parser.build_soup(markup)
            page_links = soup.select("section.pagination a")
            if not page_links:
                self._total_pages = 1
            else:
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
        return self._total_pages or 1

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
        """
        Генератор, возвращающий разметку каждой страницы пагинации.

        Args:
            start_page (int | None): Номер страницы, с которой начать. По умолчанию — 2.

        Yields:
            BeautifulSoup: Объект soup для каждой страницы.
        """
        parser = self.PAGE_PARSER(self.BASE_URL, self.features)

        # Получаем общее количество страниц один раз
        total = await self.total_pages
        logger.info(f"Обнаружено всего страниц: {total}")

        start = start_page or 2
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
