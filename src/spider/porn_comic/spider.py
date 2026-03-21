import json

from urllib.parse import urljoin

from loguru import logger
from pydantic import HttpUrl

from ...core.exc import ParserError
from ..base_spider.spider import BaseMangaSpider
from .parser import PornComicParser, PornComicPageParser


class PornComicSpider(BaseMangaSpider):
    REAL_URL = "https://www.porn-comic.com/"
    BASE_URL = "https://www.porn-comic.com/h/"
    PAGE_URL = "/index-{page}.html"
    MAX_PAGE_SELECTOR = "div.page.bigpage a"
    PAGE_PARSER = PornComicPageParser

    CUSTOM_SLEEP_TIME = 4.5
    CUSTOM_BATCH = 4

    PAGINATOR_URL = "/h/index-{page}.html"

    def __init__(self, session, manager=None, features=None, batch=None, **kwargs):
        kwargs["sleep_time"] = (
            self.CUSTOM_SLEEP_TIME
        )  # NOTE: Специально для этого сайта, так как он имеет очень строгий RATE LIMIT, и требуется задержка между запросами.
        batch = self.CUSTOM_BATCH  # NOTE: Специально для этого сайта, так как он имеет очень строгий RATE LIMIT, и требуется меньшн запросов одновременно.

        super().__init__(session, manager, features, batch, **kwargs)
        self.manga_parser = PornComicParser(
            base_url=self.BASE_URL, features=self.features
        )

    async def get(self, url, **kwargs):
        response = await self.http.get(url, "read", **kwargs)
        if response is None:
            return None

        manga = self.manga_parser.parse(response, situation="html")
        try:
            manga.gallery = [HttpUrl(x) for x in await self.get_images(url)]
        except ParserError:
            return None

        return manga

    async def get_images(self, url, **kwargs) -> list[str]:
        urls = []
        done = False

        data = await self._get_data(url, **kwargs)
        if data is None:
            return urls

        while not done:
            urls.append(data["picture"])
            if not data["has_next"]:
                done = True
                break

            data = await self._get_data(data["next_page"], **kwargs)
            if data is None:
                logger.error(
                    f"Во время парсинга одно из изображений не удалось загрузить (url={url})"
                )
                raise ParserError(
                    f"Во время парсинга одно из изображений не удалось загрузить (url={url})"
                )

        return urls

    async def _get_data(self, url, **kwargs):
        url = self.replace_url(url)
        response = await self.http.get(url, "read", **kwargs)
        if response is None:
            return None

        return self.manga_parser._parse_json(json.loads(response))

    @property
    def paginator(self):
        return self.urljoin(self.PAGINATOR_URL)

    def urljoin(self, url: str):
        return urljoin(self.REAL_URL, url)

    @staticmethod
    def replace_url(url: str) -> str:
        """Замена URL на ajax, данный отрывок был получен из файла: "https://www.porn-comic.com/statics/js/common.js" на 92 строке.

        Args:
            url (str): Первоначальный URL.

        Returns:
            str: Объединенный URL.
        """
        url = url.replace("/h/", "/ajax_h/")
        url = url.replace("/hentai/", "/ajax_hentai/")
        url = url.replace("/cos/", "/ajax_cos/")
        url = url.replace("/western/", "/ajax_western/")
        url = url.replace("/gif/", "/ajax_gif/")

        return url
