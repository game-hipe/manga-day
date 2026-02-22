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
