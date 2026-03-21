from typing import Any, Optional, TypedDict

from bs4 import BeautifulSoup

from ...core.abstract.parser import BaseMangaParser, BasePageParser
from ...core.entities.schemas import MangaSchema, BaseManga
from ...core.exc import ParserError, AttributeNotSetted, ParseSituationNotAllowed


class JsonData(TypedDict):
    picture: str
    """Изображение"""

    next_page: Optional[str]
    """Следующая страница"""

    has_next: bool
    """Есть следующая страница"""


class PornComicParser(BaseMangaParser):
    def _parse_json(self, data: dict[str, Any]) -> JsonData:
        picture: Optional[str] = data.get("pic")
        if not picture:
            raise ParserError("Не удалось извлечь picture")
        try:
            _, next = data.get("canajax")
        except ValueError:
            raise ParserError("Не удалось извлечь next")

        if not next:
            return {"picture": self._parse_picture(picture), "has_next": False}

        pager = data.get("pager")
        if not pager:
            raise ParserError("Не удалось извлечь pager")

        return {
            "picture": self._parse_picture(picture),
            "has_next": True,
            "next_page": self._parse_pager(pager),
        }

    def _parse_pager(self, pager: str) -> str:
        soup = self.build_soup(pager)
        for a in soup.select("a"):
            if a.get_text(strip=True).lower() != "next":
                continue

            if not a.get("href"):
                raise AttributeNotSetted("Не удалось извлечь href")

            return self.urljoin(a.get("href"))

    def _parse_picture(self, picture: str) -> str:
        soup = self.build_soup(picture)
        soup = soup.select_one("img")
        if not soup:
            raise AttributeNotSetted("Не удалось извлечь img")
        if not soup.get("src"):
            raise AttributeNotSetted("Не удалось извлечь src")

        return self.urljoin(soup.get("src"))

    def _parse_html(self, soup):
        title = soup.select_one("h1.title")
        poster = soup.select_one("p.manga-picture img")
        url = soup.select_one('link[hreflang="x-default"]')

        if all([title, poster, url]):
            return MangaSchema(
                title=title.get_text(strip=True),
                poster=poster.get("src"),
                url=url.get("href"),
                genres=self._parse_tags(soup),
                author=self._parse_author(soup),
                language=self._parse_language(soup),
            )

        raise AttributeNotSetted(
            "Не удалось извлечь данные из HTML. Пожалуйста, проверьте исходный код страницы."
        )

    def _parse_tags(self, soup: BeautifulSoup) -> list[str]:
        tags = []
        for a in soup.select("div.manga-tags.tag-wrap a"):
            if a.get_text(strip=True) == "":
                continue

            tags.append(a.get_text(strip=True))

        return tags

    def _parse_author(self, soup: BeautifulSoup) -> Optional[str]:
        return self._get_span_data(
            soup=soup, span_text="artist:", selector="div.summary span"
        )

    def _parse_language(self, soup: BeautifulSoup) -> Optional[str]:
        return self._get_span_data(
            soup=soup, span_text="language:", selector="div.info span"
        )

    def _get_span_data(
        self, soup: BeautifulSoup, span_text: str, selector: str
    ) -> Optional[str]:
        for span in soup.select(selector):
            if not span.next_element:
                continue

            if (
                span.next_element.get_text(strip=True).lower()
                == span_text.lower().strip()
            ):
                artist_a = span.select_one("a")
                if artist_a:
                    return artist_a.get_text(strip=True)


class PornComicPageParser(BasePageParser):
    def _parse_html(self, soup):
        mangas = []
        for li in soup.select("ul#list li"):
            url = li.select_one("a")
            poster = li.select_one("a img")
            title = li.select_one("span")

            if all([url, poster, title]):
                mangas.append(
                    BaseManga(
                        title=title.get_text(strip=True),
                        poster=self.urljoin(poster.get("src")),
                        url=self.urljoin(url.get("href")),
                    )
                )
        return mangas

    def _parse_json(self, data):
        raise ParseSituationNotAllowed("Парсинг JSON не поддерживается")
