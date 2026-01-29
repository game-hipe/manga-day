from typing import Generic, Literal, Any, TypeVar, overload
from abc import ABC, abstractmethod
from urllib.parse import urljoin

from bs4 import BeautifulSoup, _IncomingMarkup

from ..entities.schemas import MangaSchema, BaseManga

SITUATION = Literal["html", "json"]
_T = TypeVar("_T")


class BaseParser(Generic[_T], ABC):
    """Базовый парсер с поддержкой различных форматов."""

    FEATURES: str = "html.parser"
    DEFAULT_SITUATION: SITUATION = "html"

    def __init__(
        self,
        base_url: str,
        features: str | None = None,
        situation: SITUATION | None = None,
    ) -> None:
        """
        Инициализация парсера.

        Args:
            base_url: Базовый URL для разрешения относительных ссылок
            features: Парсер для BeautifulSoup (только для HTML)
            situation: Тип разметки по умолчанию
        """
        self.base_url = base_url
        self.features = features or self.FEATURES
        self.situation = situation or self.DEFAULT_SITUATION

    @overload
    def parse(
        self,
        markup: _IncomingMarkup,
        *,
        features: str | None = None,
        situation: Literal["html"] = "html",
    ) -> _T: ...

    @overload
    def parse(self, markup: Any, *, situation: Literal["json"]) -> _T: ...

    def parse(
        self,
        markup: _IncomingMarkup | Any,
        *,
        features: str | None = None,
        situation: SITUATION | None = None,
    ) -> _T:
        """
        Парсит разметку в зависимости от типа.

        Args:
            markup: HTML/JSON разметка
            features: Парсер для BeautifulSoup (используется только для HTML)
            situation: Тип разметки ('html' или 'json')

        Returns:
            Результат парсинга

        Raises:
            ValueError: Если передан неподдерживаемый тип разметки
        """
        situation = situation or self.situation

        if situation == "html":
            return self._parse_html(self.build_soup(markup, features))

        elif situation == "json":
            return self._parse_json(markup)

        raise ValueError(f"Неподдерживаемый тип разметки: {situation}")

    @abstractmethod
    def _parse_html(self, soup: BeautifulSoup) -> _T:
        """Парсит HTML-разметку."""

    @abstractmethod
    def _parse_json(self, data: Any) -> _T:
        """Парсит JSON-данные."""

    def urljoin(self, url: str) -> str:
        if url.startswith("http"):
            return url
        return urljoin(self.base_url, url)

    def build_soup(self, markup: _IncomingMarkup, features: str | None = None):
        return BeautifulSoup(markup, features or self.features)


class BaseMangaParser(BaseParser[MangaSchema]):
    """Базовый класс для парсинга манги"""


class BasePageParser(BaseParser[list[BaseManga]]):
    """Базовый класс для парсинга страниц"""
