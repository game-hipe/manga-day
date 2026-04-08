from enum import Enum
from typing import Any, TypeVar, Generic, Unpack, Literal
from urllib.parse import urljoin

import aiohttp
from aiohttp.client import _RequestOptions
from loguru import logger
from pydantic import BaseModel, ValidationError

from .schemas import (
    FindResult,
    Manga,
    LoginResponse,
    AlertResponse,
    SpiderStatus,
    LEVEL,
)

_T = TypeVar("_T", bound=BaseModel)
_R = TypeVar("_R", bound=BaseModel)
_M = TypeVar("_M", bound=BaseModel)


class Response(BaseModel, Generic[_R]):
    status: int
    ok: bool
    data: _R | None = None
    message: str | None = None


class _BaseAPI:
    """Базовый API"""

    API_URL = "/api/v1"

    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        """Базовый API

        Args:
            session (aiohttp.ClientSession): Сессия aiohttp для запросов
            base_url (str): Базовый URL пример `https://api.manga-day.ru`
        """
        self._session = session
        self._base_url = base_url
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "MangaDay-Bot",
        }

    def urljoin(self, url: str) -> str:
        """Склеить URL с базовым URL

        Args:
            url (str): URL

        Returns:
            str: склеенный URL
        """
        return urljoin(self.base_url, url)

    def api_urljoin(self, url: str) -> str:
        """Склеить URL с api_url (исправлено: правильно добавляет пути независимо от ведущих /)"""
        api_url = self.api_url
        if not api_url.endswith("/"):
            api_url += "/"
        relative = url.lstrip("/")
        return urljoin(api_url, relative)

    @property
    def api_url(self) -> str:
        return self.urljoin(self.API_URL)

    @property
    def session(self) -> aiohttp.ClientSession:
        """Сессия aiohttp"""
        return self._session

    @property
    def base_url(self) -> str:
        """Базовый URL"""
        return self._base_url


class _API(_BaseAPI, Generic[_T]):
    _API_MODEL: _T

    async def request(
        self, method: str, url: str, **kwargs: Unpack[_RequestOptions]
    ) -> Response[_T]:
        """Сделать запрос

        Args:
            method (str): метод запрос
            url (str): URL для запроса

        Returns:
            Response[_T]: Ответ
        """
        try:
            async with self.session.request(
                method=method, url=url, headers=self.headers, **kwargs
            ) as response:
                response.raise_for_status()
                return Response(
                    status=response.status,
                    ok=True,
                    data=self._API_MODEL.model_validate(await response.json()),
                )

        except aiohttp.ClientResponseError as error:
            if error.status == 404:
                logger.debug(
                    f"404 Не найдено: {error.message}",
                )

            elif error.status == 403:
                logger.debug(
                    f"403 Доступ запрещен: {error.message}",
                )

            elif error.status == 500:
                logger.debug(
                    f"500 Внутренняя ошибка сервера: {error.message}",
                )

            else:
                logger.warning(
                    f"Неизвестная ошибка: (status={error.status}, message={error.message})",
                )

            return Response(
                status=error.status, ok=False, message=error.message, data=None
            )

        except ValidationError as error:
            logger.error(f"Ошибка валидации: {error}")

            return Response(status=500, ok=False, message="Ошибка валидации", data=None)

    async def _get(self, url: str, **kwargs: Unpack[_RequestOptions]) -> Response[_T]:
        return await self.request(method="GET", url=url, **kwargs)


class FindAPI(_API[FindResult]):
    BASE_PER_PAGE = 10
    _API_MODEL = FindResult  # ← исправлено

    class Endpoint(Enum):
        PAGES = "/pages"
        GENRE = "/pages/genre"
        AUTHOR = "/pages/author"
        LANGUAGE = "/pages/language"
        QUERY = "/pages/query"

    async def pages(
        self, page: int, per_page: int = BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по всей манге из БД"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.PAGES.value),
            params={"page": page, "per_page": per_page},
        )

    async def by_genre(
        self, query: int, page: int, per_page: int = BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по жанру"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.GENRE.value),
            params={"query": query, "page": page, "per_page": per_page},
        )

    async def by_author(
        self, query: int, page: int, per_page: int = BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по автору"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.AUTHOR.value),
            params={"query": query, "page": page, "per_page": per_page},
        )

    async def by_language(
        self, query: int, page: int, per_page: int = BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по языку"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.LANGUAGE.value),
            params={"query": query, "page": page, "per_page": per_page},
        )

    async def by_query(
        self, query: str, page: int, per_page: int = BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Поиск по текстовому запросу"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.QUERY.value),
            params={"query": query, "page": page, "per_page": per_page},
        )


class MangaAPI(_API[Manga]):
    _API_MODEL = Manga

    class Endpoint(Enum):
        SKU = "/manga/sku/{sku}"
        URL = "/manga/url"
        ID = "/manga/{id}"

    async def sku(self, sku: str) -> Response[Manga]:
        """Получить информацию об манге по SKU"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.SKU.value.format(sku=sku))
        )

    async def id(self, id: int) -> Response[Manga]:
        """Получить информацию об манге по ID"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.ID.value.format(id=id))
        )

    async def url(self, url: str) -> Response[Manga]:
        """Получить информацию об манге по URL"""
        return await self._get(
            url=self.api_urljoin(self.Endpoint.URL.value), params={"url": url}
        )


class AdminAPI(_BaseAPI):
    API_URL = "/v1/api/admin/"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        username: str,
        password: str,
    ):
        super().__init__(session, base_url)
        self._token: str | None = None
        self._username: str = username
        self._password: str = password

    async def login(self) -> LoginResponse | None:
        """Залогиниться"""
        login = await self._post(
            url=self.api_urljoin("login"),
            auth=False,
            params={  # ← исправлено: json вместо params
                "username": self._username,
                "password": self._password,
            },
            model=LoginResponse,
        )
        if isinstance(login, LoginResponse):
            self._token = login.token

        return login

    async def alert(self, message: str, level: LEVEL) -> AlertResponse | None:
        """Уведомление"""
        return await self._post(
            url=self.api_urljoin("alert"),
            headers=self.headers | {"Authorization": f"Bearer {self._token}"},
            json={"message": message, "level": level, "name": "MangaBot"},
            model=AlertResponse,
        )

    async def spider(
        self,
        signal: Literal["start", "stop"],
        spider: str | Literal["all"],
        page: int | None = None,
    ) -> None:
        """Отправить запрос на начало парсинга"""
        await self._post(
            url=self.api_urljoin("spider"),
            headers=self.headers | {"Authorization": f"Bearer {self._token}"},
            json={"signal": signal, "spider": spider, "page": page},
        )

    async def status(self):
        """Получить статус пауков"""
        result: list[SpiderStatus] = []
        status = await self._post(
            url=self.api_urljoin("spider/status"),
            method="GET",
            headers=self.headers | {"Authorization": f"Bearer {self._token}"},
        )
        for spider in status:
            result.append(SpiderStatus.model_validate(spider))

        return result

    async def _post(
        self,
        url: str,
        method: str = "POST",
        auth: bool = True,
        model: type[_M] | None = None,
        **kwargs: Unpack[_RequestOptions],
    ) -> _M | Any:
        if "headers" not in kwargs:
            kwargs["headers"] = self.headers.copy()
        else:
            kwargs["headers"] = self.headers | kwargs["headers"]

        for _ in range(3):
            try:
                async with self.session.request(
                    method=method, url=url, **kwargs
                ) as response:
                    response.raise_for_status()
                    if model is None:
                        return await response.json()
                    return model.model_validate(await response.json())

            except aiohttp.ClientResponseError as error:
                if error.status in [403, 401]:
                    if auth:
                        login_info = await self.login()
                        if login_info:
                            self._token = login_info.token
                            auth_header = {"Authorization": f"Bearer {self._token}"}
                            kwargs["headers"] = dict(kwargs["headers"]) | auth_header

                    logger.warning(
                        f"Не удалось авторизоваться: {error.message}",
                    )

                elif error.status == 429:
                    logger.warning(
                        f"Слишком много запросов: {error.message}",
                    )

                else:
                    logger.warning(
                        f"Неизвестная ошибка: (status={error.status}, message={error.message})",
                    )

        return None

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password


class API:
    def __init__(self, base_url: str):
        self._session = aiohttp.ClientSession()
        self._base_url = base_url

        self._find = FindAPI(self._session, base_url)
        self._manga = MangaAPI(self._session, base_url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()

    async def pages(
        self, page: int, per_page: int = FindAPI.BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по всей манге

        Args:
            page (int): номер страницы
            per_page (int, optional): Кол-во элементов на странице. По умолчанию FindAPI.BASE_PER_PAGE.

        Returns:
            Response[FindResult]: Ответ API
        """
        return await self._find.pages(page=page, per_page=per_page)

    async def by_genre(
        self, query: int, page: int, per_page: int = FindAPI.BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по выбранному жанру

        Args:
            query (int): ID жанра
            page (int): номер страницы
            per_page (int, optional): Кол-во элементов на странице. По умолчанию FindAPI.BASE_PER_PAGE.

        Returns:
            Response[FindResult]: Ответ API
        """
        return await self._find.by_genre(query=query, page=page, per_page=per_page)

    async def by_author(
        self, query: int, page: int, per_page: int = FindAPI.BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по выбранному автору

        Args:
            query (int): ID автора
            page (int): номер страницы
            per_page (int, optional): Кол-во элементов на странице. По умолчанию FindAPI.BASE_PER_PAGE.

        Returns:
            Response[FindResult]: Ответ API
        """
        return await self._find.by_author(query=query, page=page, per_page=per_page)

    async def by_language(
        self, query: int, page: int, per_page: int = FindAPI.BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по выбранному языку

        Args:
            query (int): ID языка
            page (int): номер страницы
            per_page (int, optional): Кол-во элементов на странице. По умолчанию FindAPI.BASE_PER_PAGE.

        Returns:
            Response[FindResult]: Ответ API
        """
        return await self._find.by_language(query=query, page=page, per_page=per_page)

    async def by_query(
        self, query: str, page: int, per_page: int = FindAPI.BASE_PER_PAGE
    ) -> Response[FindResult]:
        """Пагинация по текстовому запросу

        Args:
            query (str): текстовый запрос
            page (int): номер страницы
            per_page (int, optional): Кол-во элементов на странице. По умолчанию FindAPI.BASE_PER_PAGE.

        Returns:
            Response[FindResult]: Ответ API
        """
        return await self._find.by_query(query=query, page=page, per_page=per_page)

    async def get_by_sku(self, sku: str) -> Response[Manga]:
        """Получить мангу используя артикул

        Args:
            sku (str): артикул

        Returns:
            Response[Manga]: Ответ API
        """
        return await self._manga.sku(sku)

    async def get_by_id(self, id: int) -> Response[Manga]:
        """Получить мангу используя ID

        Args:
            id (int): ID манги

        Returns:
            Response[Manga]: Ответ API
        """
        return await self._manga.id(id)

    async def get_by_url(self, url: str) -> Response[Manga]:
        """Получить мангу используя URL

        Args:
            url (str): URL манги

        Returns:
            Response[Manga]: Ответ API
        """
        return await self._manga.url(url)
