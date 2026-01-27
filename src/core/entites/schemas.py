import hashlib

from aiohttp import BasicAuth
from pydantic import BaseModel, HttpUrl, Field


class BaseManga(BaseModel):
    """
    Схема для хранение базовой версии манги

    Args:
        title (str): название манги
        url (HttpUrl): ссылка на мангу
        poster (HttpUrl): ссылка на постер манги
    """

    title: str
    poster: HttpUrl
    url: HttpUrl

    @property
    def sku(self) -> str:
        """Генерирует sku"""
        if self.title and self.url:
            data = f"{self.title}{self.url.encoded_string()}".encode("utf-8")
            return hashlib.sha256(data).hexdigest()[:32]


class MangaSchema(BaseManga):
    """
    Схема для хранения версии манги с дополнительными данными (Наследуется от BaseManga)

    Args:
        genres (list[str]): список жанров (строки)
        author (str | None): автор манги
        language (str | None): язык манги
        gallery (list[HttpUrl]): список ссылок на изображения
    """

    genres: list[str] = Field(default_factory=list)
    author: str | None = Field(default=None)
    language: str | None = Field(default=None)

    gallery: list[HttpUrl] = Field(default_factory=list)


class OutputMangaSchema(MangaSchema):
    """
    Схема для хранении версии манги из БД

    Args:
        id (int): Внутренний ID либо сайта, либо БД
    """

    id: int


class FiltersSchema(BaseModel):
    """
    Схема для хранения фильтров поиска

    Args:
        title (str | None): название манги
        author (str | None): автор манги
        language (str | None): язык манги
        genres (list[str]): список жанров (строки)
    """

    title: str | None = Field(default=None)
    author: str | None = Field(default=None)
    language: str | None = Field(default=None)
    genres: list[str] = Field(default_factory=list)


class ProxySchema(BaseModel):
    """
    Схема данных для настройки прокси-сервера с аутентификацией

    Args:
        proxy (str): ip адрес сервера
        login (str | None): логин для авторизации
        password (str | None): пароль для авторизации
    """

    proxy: str
    login: str | None = Field(default=None)
    password: str | None = Field(default=None)

    def auth(self) -> dict[str, str | BasicAuth]:
        return {
            "proxy": self.proxy,
            "proxy_auth": BasicAuth(login=self.login, password=self.password or "")
            if self.login
            else None,
        }
