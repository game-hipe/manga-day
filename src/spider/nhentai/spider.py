from ..base_spider.spider import BaseMangaSpider
from .parser import NhentaiMangaParser, NhentaiPageParser


class NhentaiSpider(BaseMangaSpider):
    REAL_URL = "https://nhentai.to"
    BASE_URL = "https://nhentai.to/go"
    PAGE_URL = "//?page={page}"
    PAGE_PARSER = NhentaiPageParser
    MANGA_PARSER = NhentaiMangaParser

    async def get(self, url, **kw):
        response = await self.http.get(url, "read", **kw)

        if response is None:
            return None

        parser = self.MANGA_PARSER(self.REAL_URL, self.features)
        data = parser.parse(response, situation="html")

        return data
