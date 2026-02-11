import asyncio
import random
from typing import TypedDict, TypeVar, Generic, Unpack

from cachetools import TTLCache

from ..entities.schemas import ProxySchema


_T = TypeVar("_T")


class RequestItem(TypedDict):
    """Аргументы для запросов"""

    max_concurrents: int | None = (None,)
    """Максимальное количество запросов одновременно."""

    max_retries: int | None = (None,)
    """Максимальное количество попыток."""

    sleep_time: int | None = (None,)
    """Время сна после запроса."""

    use_random: bool | None = (None,)
    """Использовать ли рандом во время ожидания."""

    proxy: list[ProxySchema] | None = (None,)
    """Прокси"""
    maxsize: int | None = (None,)
    """Максимальный размер кэша."""

    ttl: float | None = None
    """Время жизни кэша."""


class BaseRequestManager(Generic[_T]):
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

    def __init__(self, session: _T, **kw: Unpack[RequestItem]):
        """Ицилизация RequestManager

        Args:
            session (_T): Сессия для работы с запросами.
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

    async def sleep(self, time: float | None = None):
        await asyncio.sleep(
            (time or self.sleep_time) * (random.uniform(0, 1) if self.use_random else 1)
        )
