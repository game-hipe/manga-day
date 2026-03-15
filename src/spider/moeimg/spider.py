from urllib.parse import urlparse
from pydantic import HttpUrl

from .parser import MoeImgParser
from ..hitomi.parser import HitomiPageParser
from ..hitomi.spider import HitomiSpider


class MoeImgSpider(HitomiSpider):
    HAS_CLOUDFARE = False
    START_PAGE = 1

    MANGA_PARSER = MoeImgParser
    PAGE_PARSER = HitomiPageParser

    PAGE_URL = "/latest?page={page}"
    BASE_URL = "https://moeimg.fan"

    SUFFIX: str = "fa"

    async def get(
        self, url, **kwargs
    ):  # Данная строка добавлена по причине того что moeimg может ошибочно вернуть hitomiKr.
        manga = await super().get(url, **kwargs)
        if manga:
            parsed = urlparse(str(manga.poster))
            path = parsed.path
            manga.poster = HttpUrl(f"{self.BASE_URL.rstrip('/')}/{path.lstrip('/')}")
        return manga
