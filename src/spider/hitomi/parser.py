from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger

from ...core.abstract.parser import BaseMangaParser, BasePageParser
from ...core.entities.schemas import MangaSchema

class HitomiMangaParser(BaseMangaParser):
    def _parse_html(self, soup):
        logger.debug("Парсинг данных тип (HTML)")
        title = soup.select_one('h1')
        url = soup.select_one('link[rel="canonical"]')
        poster = soup.select_one('div.img-holder img')
        
        genres = self.extract_tags(soup, "标签")
        author = self.extract_tags(soup, "作者")
        language = self.extract_tags(soup, "语言")
        
        if all([title, poster, url]):
            title = title.get_text(strip=True)
            poster = self.urljoin(poster.get("src"))
            url = url.get("href")
        else:
            raise ValueError(
                "Не удалось извлечь данные из HTML. Пожалуйста, проверьте исходный код страницы."
            )
            
        return MangaSchema(
            title = title,
            poster = poster,
            url = url,
            genres = genres,
            author = author[0] if author else None,
            language = language[0] if language else None
        )
        
    def _parse_json(self, data) -> list[str]:
        logger.debug("Парсинг данных тип (JSON)")
        result: str = data.get(
            "chapter_detail", {}
        ).get("chapter_content", None)
        
        server: str = data.get(
            "chapter_detail", {}
        ).get("server", None)
        
        soup = self.build_soup(result)
        return [urljoin(
            server, img['data-url']
        ) for img in soup.select("img") if img.get("data-url")]
        
    def extract_tags(self, soup: BeautifulSoup, tag_name: str) -> list[str]:
        for br in soup.select('div.manga-detail ul li.br'):
            if (title := br.select_one("div.md-title")) is None:
                continue
            
            elif title.get_text(strip=True) != tag_name + ":":
                continue
            
            return [x.get('title') for x in br.select("div.md-content a") if x.get('title')]
        
        return []

class HitomiPageParser(BasePageParser):
    def _parse_html(self, soup):
        ...
        
    def _parse_json(self, data):
        raise AttributeError(
            "Этот парсер не поддерживает данные в формате JSON. Пожалуйста, используйте HTML-анализатор."
        )