import asyncio

from abc import ABC, abstractmethod
from typing import overload, AsyncGenerator, Awaitable, Optional, Any

import aiohttp

from ..manager.manga import MangaManager
from ..manager.request import RequestManager
from ..entites.schemas import ProxySchema, MangaSchema, BaseManga

class BaseSpider(ABC):
    """
    Базовый класс для создания спайдеров, предназначенных для парсинга информации о манге с веб-сайтов.

    Атрибуты:
        BASE_URL (str): Базовый URL-адрес сайта, с которого будет выполняться парсинг. Должен быть переопределён в подклассах.
    """
    
    BASE_URL = "https://example-manga.com"
    """Базовый класс для спайдера"""
    
    BASE_FEATURES = 'html.parser'
    """Базовый движок для парсера"""
    
    @overload
    def __init__(self, session: RequestManager, manager: MangaManager, features: str = None) -> None:
        """
        Инициализация спайдера с использованием существующего менеджера запросов.

        Аргументы:
            session (RequestManager): Управляемая сессия для выполнения HTTP-запросов.
            manager (MangaManager): Менеджер для обработки и хранения данных о манге.
            features (str): Парсер, используемый для разбора HTML (по умолчанию 'html.parser').
        """
    
    @overload
    def __init__(
        self,
        session: aiohttp.ClientSession,
        manager: MangaManager,
        features: str = None,
        *,
        max_concurrents: int = None,
        max_retries: int = None,
        sleep_time: int = None,
        use_random: bool = None,
        maxsize: int = None,
        ttl: float = None,
        proxy: list[ProxySchema] = [],
    ) -> None:
        """
        Инициализация спайдера с использованием aiohttp.ClientSession.

        Аргументы:
            session (aiohttp.ClientSession): Сессия для асинхронных HTTP-запросов.
            manager (MangaManager): Менеджер для обработки и хранения данных о манге.
            features (str): Парсер, используемый для разбора HTML (по умолчанию 'html.parser').
            max_concurrents (int, опционально): Максимальное количество одновременных запросов.
            max_retries (int, опционально): Максимальное количество попыток повтора запроса.
            sleep_time (int, опционально): Время задержки между запросами.
            use_random (bool, опционально): Использовать ли случайную задержку.
            maxsize (int, опционально): Максимальный размер кеша запросов.
            ttl (float, опционально): Время жизни кешированных запросов.
            proxy (list[ProxySchema], опционально): Список прокси для использования.
        """
    
    def __init__(self, session: aiohttp.ClientSession | RequestManager, manager: MangaManager, features: str = None, **kwargs) -> None:
        """
        Инициализация базового спайдера.

        Аргументы:
            session (aiohttp.ClientSession | RequestManager): Сессия или менеджер запросов.
            manager (MangaManager): Менеджер для управления данными о манге.
            features (str): Парсер HTML (по умолчанию 'html.parser').
            **kwargs: Дополнительные параметры, передаваемые в RequestManager при необходимости.

        Исключения:
            TypeError: Если session не является ни ClientSession, ни RequestManager.
        """
        if isinstance(session, RequestManager):
            self.http = session
            
        elif isinstance(session, aiohttp.ClientSession):
            self.http = RequestManager(session, **kwargs)
            
        else:
            raise TypeError("Сессия должна быть aiohttp.ClientSession либо RequestManager")
        
        self.features = features or self.BASE_FEATURES
        self.manager = manager
        
        self._args_test()
        
    async def run(self) -> None:
        """
        Запускает процесс парсинга манги.

        Метод последовательно получает пакеты страниц, извлекает информацию о манге
        и добавляет её в менеджер. Пропускает пустые результаты.
        """
        async for page_batch in self.pages():
            tasks: list[Awaitable[Optional[MangaSchema]]] = []
            for page in page_batch:
                tasks.append(asyncio.create_task(self.get(str(page.url))))

            async for manga in asyncio.as_completed(tasks):
                result = await manga
                if result is None:
                    continue
                
                await self.manager.add_manga(result)

    @abstractmethod
    async def get(self, url: str) -> Optional[MangaSchema]:
        """
        Абстрактный метод для получения данных о манге по URL.

        Аргументы:
            url (str): Ссылка на страницу манги.

        Возвращает:
            MangaSchema | None: Объект с данными о манге или None, если не удалось получить данные.
        """

    @abstractmethod
    async def pages(self) -> AsyncGenerator[list[BaseManga], Any]:
        """
        Абстрактный метод для генерации пакетов URL-адресов страниц с мангой.

        Возвращает:
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

        if not isinstance(self.manager, MangaManager):
            raise TypeError(
                "manager должен быть MangaManager"
            )