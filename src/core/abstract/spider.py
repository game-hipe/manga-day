import asyncio

from urllib.parse import urljoin
from abc import ABC, abstractmethod
from typing import overload, AsyncGenerator, Awaitable, Optional, Any, Unpack

import aiohttp

from loguru import logger

from ..manager.manga import MangaManager
from ..manager.request import RequestManager, RequestItem
from ..entities.schemas import MangaSchema, BaseManga


class BaseSpider(ABC):
    """
    Базовый класс для создания спайдеров, предназначенных для парсинга информации о манге с веб-сайтов.

    Атрибуты:
        BASE_URL (str): Базовый URL-адрес сайта, с которого будет выполняться парсинг. Должен быть переопределён в подклассах.
    """

    BASE_URL = "https://example-manga.com"
    """Базовый класс для спайдера"""

    BASE_FEATURES = "html.parser"
    """Базовый движок для парсера"""

    BASE_BATCH = 10
    """Базовый размер пачки для парсинга"""

    @overload
    def __init__(
        self,
        session: RequestManager,
        manager: MangaManager | None = None,
        features: str = None,
        batch: int = None,
    ) -> None:
        """
        Инициализация спайдера с использованием существующего менеджера запросов.

        Args:
            session (RequestManager): Управляемая сессия для выполнения HTTP-запросов.
            manager (MangaManager | None): Менеджер для обработки и хранения данных о манге. Если менеджер является None то функция "run" перестает работать. (по умолчанию None).
            features (str): Парсер, используемый для разбора HTML (по умолчанию 'html.parser').
            batch (int): Размер пачки для парсинга (по умолчанию 10).
        """

    @overload
    def __init__(
        self,
        session: aiohttp.ClientSession,
        manager: MangaManager,
        features: str = None,
        batch: int = None,
        **kwargs: Unpack[RequestItem],
    ) -> None:
        """
        Инициализация спайдера с использованием aiohttp.ClientSession.

        Args:
            session (aiohttp.ClientSession): Сессия для асинхронных HTTP-запросов.
            manager (MangaManager): Менеджер для обработки и хранения данных о манге. Если менеджер является None то функция "run" перестает работать. (по умолчанию None).
            features (str): Парсер, используемый для разбора HTML (по умолчанию 'html.parser').
            batch (int): Размер пачки для парсинга (по умолчанию 10).
            max_concurrents (int, опционально): Максимальное количество одновременных запросов.
            max_retries (int, опционально): Максимальное количество попыток повтора запроса.
            sleep_time (int, опционально): Время задержки между запросами.
            use_random (bool, опционально): Использовать ли случайную задержку.
            maxsize (int, опционально): Максимальный размер кеша запросов.
            ttl (float, опционально): Время жизни кешированных запросов.
            proxy (list[ProxySchema], опционально): Список прокси для использования.
        """

    def __init__(
        self,
        session: aiohttp.ClientSession | RequestManager,
        manager: MangaManager | None = None,
        features: str = None,
        batch: int = None,
        **kwargs,
    ) -> None:
        """
        Инициализация базового спайдера.

        Args:
            session (aiohttp.ClientSession | RequestManager): Сессия или менеджер запросов.
            manager (MangaManager): Менеджер для управления данными о манге. Если менеджер является None то функция "run" перестает работать. (по умолчанию None).
            features (str): Парсер HTML (по умолчанию 'html.parser').
            batch (int): Размер пачки для парсинга (по умолчанию 10).
            **kwargs: Дополнительные параметры, передаваемые в RequestManager при необходимости.

        Исключения:
            TypeError: Если session не является ни ClientSession, ни RequestManager.
        """
        if isinstance(session, RequestManager):
            self.http = session

        elif isinstance(session, aiohttp.ClientSession):
            self.http = RequestManager(session, **kwargs)

        else:
            raise TypeError(
                "Сессия должна быть aiohttp.ClientSession либо RequestManager"
            )

        self.batch = batch or self.BASE_BATCH
        self.features = features or self.BASE_FEATURES
        self.manager = manager

        self._args_test()
        logger.debug(f"Инцилизирован класс {self.__class__.__name__}")

    async def run(self, start_page: int | None = None) -> None:
        """
        Запускает процесс парсинга манги.

        Метод последовательно получает пакеты страниц, извлекает информацию о манге
        и добавляет её в менеджер. Пропускает пустые результаты.

        Args:
            start_page (int | None): Стартовая страница для парсинга.
        """
        if self.manager is None:
            raise AttributeError("Менеджер не был передан, функция 'run' не работает")

        async for page_batch in self.pages(start_page):
            tasks: list[Awaitable[Optional[MangaSchema]]] = []
            for page in page_batch:
                if await self.manager.in_database(page):
                    continue

                tasks.append(asyncio.create_task(self.get(str(page.url))))

            async for manga in asyncio.as_completed(tasks):
                result = await manga
                if result is None:
                    continue

                if not result.gallery:
                    logger.warning(
                        f"Не удалось получить галерею (url={result.url}, title={result.title})"
                    )

                await self.manager.add_manga(result)

    @abstractmethod
    async def get(self, url: str) -> Optional[MangaSchema]:
        """
        Абстрактный метод для получения данных о манге по URL.

        Args:
            url (str): Ссылка на страницу манги.

        Returns:
            MangaSchema | None: Объект с данными о манге или None, если не удалось получить данные.
        """

    @abstractmethod
    async def pages(
        self, start_page: int | None = None
    ) -> AsyncGenerator[list[BaseManga], Any]:
        """
        Абстрактный метод для генерации пакетов URL-адресов страниц с мангой.

        Args:
            start_page (int): Стартовая страница для парсинга.

        Returns:
            Асинхронный генератор, выдающий списки базовйх манг (BaseManga).
        """
        yield []

    def _args_test(self) -> None:
        """
        Проверяет корректность аргументов при инициализации.

        Исключения:
            NotImplementedError: Если BASE_URL остался неизменным (по умолчанию).
            TypeError: Если manager не является экземпляром MangaManager.
        """
        if self.BASE_URL == "https://example-manga.com":
            raise NotImplementedError(
                "BASE_URL не должен быть https://example-manga.com"
            )

        if self.manager is None:
            logger.warning("Менеджер не был передан, функция 'run' перестанет работать")

        elif not isinstance(self.manager, MangaManager):
            raise TypeError("manager должен быть MangaManager")

    def urljoin(self, url: str) -> str:
        """
        Объединяет базовый URL с относительным.

        Args:
            url (str): Относительный URL.

        Returns:
            str: Объединенный URL.
        """
        return urljoin(self.BASE_URL, url)
