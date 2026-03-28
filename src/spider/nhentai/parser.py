from urllib.parse import urljoin

from ...core.abstract.parser import BaseMangaParser
from ...core.entities.schemas import MangaSchema
from ...core.exc import ParserError, ParseSituationNotAllowed
from ..base_spider.parser import GlobalPageParser


class NhentaiMangaParser(BaseMangaParser):
    TAGS = {"tags": "genres", "artists": "author", "languages": "language"}

    def _parse_html(self, soup):
        title = soup.select_one("div#info h1")
        poster = soup.select_one("div#cover img")
        url = soup.select_one("#gallery_id")

        if all([title, poster, url]):
            title = title.get_text(strip=True)
            poster = poster.get("src")
            url = self.urljoin(
                "/g/" + "".join(x for x in url.get_text(strip=True) if x.isdigit())
            )
        else:
            raise ParserError(
                "Не удалось извлечь данные из HTML. Пожалуйста, проверьте исходный код страницы."
            )
        _tags = soup.select("section#tags div.tag-container")
        tags = {}

        for tag in _tags:
            if tag.next_element is None:
                continue

            tag_name = tag.next_element.get_text(strip=True).lower()
            if tag_name in self.TAGS:
                if self.TAGS[tag_name] == "genres":
                    tags[self.TAGS[tag_name]] = list(
                        set(t.get_text() for t in tag.select("a.tag span.name"))
                    )

                else:
                    tags[self.TAGS[tag_name]] = (
                        tag.select_one("a.tag span.name").get_text(strip=True)
                        if tag.select_one("a.tag span.name")
                        else None
                    )

        gallery = [
            self._fix_gallery_url(self.urljoin(img.get("data-src")))
            for img in soup.select("div#thumbnail-container img")
            if img.get("data-src")
        ]

        if all([title, poster, url]):
            return MangaSchema(
                title=title, poster=poster, url=url, gallery=gallery, **tags
            )

        raise ParserError(
            "Не удалось извлечь данные из HTML. Пожалуйста, проверьте исходный код страницы."
        )

    def _parse_json(self, data):
        raise ParseSituationNotAllowed(
            "Этот парсер не поддерживает данные в формате JSON. Пожалуйста, используйте HTML-анализатор."
        )

    def _fix_gallery_url(self, url: str) -> str:
        file = url.split("/")[-1]
        file_name, suffix = file.split(".")

        return urljoin(url, file_name.replace("t", "") + "." + suffix)


class NhentaiPageParser(GlobalPageParser):
    SELECTOR = "div.container.index-container .gallery"
