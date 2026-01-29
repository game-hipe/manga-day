import asyncio
import random
from typing import Unpack, Literal, TypeAlias, TypedDict, overload

from aiohttp import ClientSession
from aiohttp import ClientResponseError, ServerDisconnectedError
from aiohttp.client import _RequestOptions

from cachetools import TTLCache
from loguru import logger

from ..entities.schemas import ProxySchema

ReturnType: TypeAlias = Literal["text", "read"]


class RequestItem(TypedDict):
    max_concurrents: int | None = (None,)
    max_retries: int | None = (None,)
    sleep_time: int | None = (None,)
    use_random: bool | None = (None,)
    proxy: list[ProxySchema] | None = (None,)
    maxsize: int | None = (None,)
    ttl: float | None = None


class RequestManager:
    """Менеджер для запросов."""

    SLEEP_TIME: int = 2
    """Базовое время сна, после запроса."""

    USE_RANDOM: int = True
    """Базовое значение, использование рандома при ожидании"""

    MAX_CONCURRENTS: int = 5
    """Базовое значение, количество запросов одновременно"""

    MAX_RETRIES: int = 3
    """Базовое значение, максимальное количество попыток."""

    MAXSIZE: int = 128
    """Базовое значение, максимального размера кэша."""

    TTL: float = 300
    """Базовое значение, время жизни кэша."""

    def __init__(self, session: ClientSession, **kw: Unpack[RequestItem]):
        """Ицилизация RequestManager

        Args:
            session (ClientSession): Сессия aiohttp.
            max_concurrents (int, None, optional): Максимальное количество запросов.
            max_retries (int, None, optional): Максимальное количество попыток.
            sleep_time (int, None, optional): Время сна после запроса. Обычное значени SLEEP_TIME.
            use_random (bool, optional): Использовать ли рандом во время ожидания. Обычное значени USE_RANDOM.
            proxy (list[ProxySchema], optional): Прокси. Обычное значение [].
        """
        self.session = session
        self.max_concurrents = kw.get("max_concurrents") or self.MAX_CONCURRENTS
        self.max_retries = kw.get("max_retries") or self.MAX_RETRIES
        self.sleep_time = kw.get("sleep_time") or self.SLEEP_TIME
        self.use_random = kw.get("use_random") or self.USE_RANDOM

        self.semaphore = asyncio.Semaphore(self.max_concurrents)
        self.proxy = [] or kw.get("proxy")

        self.cache = TTLCache(
            maxsize=kw.get("maxsize") or self.MAXSIZE, ttl=kw.get("ttl") or self.TTL
        )

    @overload
    async def request(
        self,
        method: str,
        url: str,
        type: Literal["text"],
        **kwargs: Unpack[_RequestOptions],
    ) -> str | None:
        """Функция, для запросов с системой повторных попыток.

        Args:
            method (str): Метод, для получение страницы (GET, POST, и т п.)
            url (str): Путь к интернет странице
            type (Literal["text"]): Возращает текст страницы

        Returns:
            str | None: Возращает текст страницы
        """

    @overload
    async def request(
        self,
        method: str,
        url: str,
        type: Literal["read"],
        **kwargs: Unpack[_RequestOptions],
    ) -> bytes | None:
        """Функция, для запросов с системой повторных попыток.

        Attributes:
            method (str): Метод, для получение страницы (GET, POST, и т п.)
            url (str): Путь к интернет странице
            type (Literal["read"]): Возращает бинарные данные

        Returns:
            bytes | None: Возращает данные с страницы
        """

    @overload
    async def get(
        self, url: str, type: Literal["text"], **kwargs: Unpack[_RequestOptions]
    ) -> str | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут GET

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["text"]): Возращает текст страницы

        Returns:
            str | None: Возращает текст страницы
        """

    @overload
    async def get(
        self, url: str, type: Literal["read"], **kwargs: Unpack[_RequestOptions]
    ) -> bytes | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут GET

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["read"]): Возращает бинарные данные

        Returns:
            bytes | None: Возращает данные с страницы
        """

    @overload
    async def post(
        self, url: str, type: Literal["text"], **kwargs: Unpack[_RequestOptions]
    ) -> str | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут POST

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["text"]): Возращает текст страницы

        Returns:
            str | None: Возращает текст страницы
        """

    @overload
    async def post(
        self, url: str, type: Literal["read"], **kwargs: Unpack[_RequestOptions]
    ) -> bytes | None:
        """Функция, для запросов с системой повторных попыток. имеет готовый атрибут POST

        Attributes:
            url (str): Путь к интернет странице
            type (Literal["read"]): Возращает бинарные данные

        Returns:
            bytes | None: Возращает данные с страницы
        """

    async def request(
        self, method: str, url: str, type: ReturnType, **kwargs: Unpack[_RequestOptions]
    ) -> str | bytes | None:
        """Функция, для запросов с системой повторных попыток.

        Attributes:
            method (str): Метод, для получение страницы (GET, POST, и т п.)
            url (str): Путь к интернет странице
            type (str): тип возращаемых данных

        Returns:
            str | bytes | None: Возращает данные с страницы
        """
        if f"{method}{url}" in self.cache:
            logger.info(f"Используется кэш (url={url}, method={method})")
            return self.cache[f"{method}{url}"]

        async with self.semaphore:
            logger.info(f"Попытка получить страницу (url={url}, method={method})")
            for _ in range(self.max_retries):
                try:
                    async with self.session.request(
                        method, url, **kwargs, **self._get_proxy()
                    ) as response:
                        response.raise_for_status()
                        result = await getattr(response, type)()
                        logger.info(
                            f"Удалось получить страницу (url={url}, method={method}, result_len={len(result)})"
                        )
                        self.cache[f"{method}{url}"] = result
                        return result

                except ClientResponseError as error:
                    if error.status == 404:
                        logger.warning(
                            f"Страницы не существует (url={url}, method={method})"
                        )
                        return

                    elif error.status == 403:
                        logger.warning(
                            f"Страница недоступна (url={url}, method={method}, message={error.message})"
                        )
                        return

                    logger.error(
                        f"Не удалось получить страницу (url={url}, method={method}, message={error.message})"
                    )

                except ServerDisconnectedError:
                    logger.error("Сервер принудительно отключил нас от сервера.")

                finally:
                    await asyncio.sleep(
                        self.sleep_time
                        * (random.uniform(0, 1) if self.use_random else 1)
                    )

            logger.error(f"Не удалось получить страницу за {self.max_retries} попыток")

    async def get(
        self, url: str, type: ReturnType, **kwargs: Unpack[_RequestOptions]
    ) -> str | bytes | None:
        return await self.request("GET", url, type=type, **kwargs)

    async def post(
        self, url: str, type: ReturnType, **kwargs: Unpack[_RequestOptions]
    ) -> str | bytes | None:
        return await self.request("POST", url, type=type, **kwargs)

    def _get_proxy(self):
        if not self.proxy:
            return {}

        proxy = random.choice(self.proxy)
        return proxy.auth()
