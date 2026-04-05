from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from slowapi import Limiter

from ...core import __version__
from ...core.service import FindService
from ...core.entities.schemas import (
    ApiOutputManga,
    OutputMangaSchema,
    MangaFindResultSchema,
    ObjectWithId,
)


def pagination(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int | None = Query(
        None, ge=1, le=100, description="Количество на странице"
    ),
):
    return {
        "page": page,
        "per_page": per_page,
    }


class Endpoints:
    """Эндпоинты для API манги."""

    BASE_LIMIT = 60

    MANGA_LIMIT = 60

    PAGINATION_LIMIT = 120

    def __init__(self, service: FindService, bot: str, limiter: Limiter):
        """Инициализация Endpoints

        Args:
            service (FindService): Сервис для работы с мангой.
            bot (str): URL бота Telegram.
            limiter (Limiter): Лимит запросов
        """
        self.service = service
        self.bot = bot
        self._router = APIRouter(prefix="/api/v1")
        self.limiter = limiter

        self._setup_routes()
        self._setup_tag_routes()
        self._setup_finder_routes()

        self._setup_tools()

    def _setup_tools(self):
        """Настройка инструментов."""

        self._router.add_api_route(
            "/bot",
            self.get_bot_url,
            methods=["GET"],
            response_model=str,
            summary="Получить URL бота",
            tags=["tools"],
        )

        self._router.add_api_route(
            "/health",
            self.health,
            methods=["GET"],
            tags=["tools"],
            summary="Проверка работоспособности",
        )

    def _setup_routes(self):
        """
        Настройка роутера добавление новых поинтов
        """
        self._router.add_api_route(
            "/manga/sku/{sku}",
            self._func_with_limit(self.get_manga_by_sku, f"{self.MANGA_LIMIT}/minute"),
            response_model=ApiOutputManga,
            summary="Получить мангу по SKU",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/url",
            self._func_with_limit(self.get_manga_by_url, f"{self.MANGA_LIMIT}/minute"),
            methods=["GET"],
            response_model=ApiOutputManga,
            summary="Получить мангу по URL",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/{id}",
            self._func_with_limit(self.get_manga, f"{self.MANGA_LIMIT}/minute"),
            methods=["GET"],
            response_model=ApiOutputManga,
            summary="Получить мангу по внутреннему ID в БД",
            tags=["manga"],
        )

    def _setup_finder_routes(self):
        self._router.add_api_route(
            "/pages",
            self._func_with_limit(self.get_pages, f"{self.PAGINATION_LIMIT}/minute"),
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по страницам",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/genre",
            self._func_with_limit(
                self.get_pages_by_genre, f"{self.PAGINATION_LIMIT}/minute"
            ),
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по жанру",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/author",
            self._func_with_limit(
                self.get_pages_by_author, f"{self.PAGINATION_LIMIT}/minute"
            ),
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по автору",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/language",
            self._func_with_limit(
                self.get_pages_by_language, f"{self.PAGINATION_LIMIT}/minute"
            ),
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по языку",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/query",
            self._func_with_limit(
                self.get_pages_by_query, f"{self.PAGINATION_LIMIT}/minute"
            ),
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по запросу",
            tags=["find"],
        )

    def _setup_tag_routes(self):
        self._router.add_api_route(
            "/genres",
            self._func_with_limit(self.get_all_genres),
            methods=["GET"],
            response_model=list[ObjectWithId],
            summary="Получить список жанров",
            tags=["Tags"],
        )

        self._router.add_api_route(
            "/language",
            self._func_with_limit(self.get_all_languages),
            methods=["GET"],
            response_model=list[ObjectWithId],
            summary="Получить список языков",
            tags=["Tags"],
        )

        self._router.add_api_route(
            "/author",
            self._func_with_limit(self.get_authors),
            methods=["GET"],
            response_model=list[ObjectWithId],
            summary="Получить список авторов",
            tags=["Tags"],
        )

    async def get_pages(
        self, request: Request, common: dict = Depends(pagination)
    ) -> MangaFindResultSchema:
        """Получить страницу.

        Args:
            page (int): Номер страницы
            per_page (int, optional): Количество манги на странице. По умолчанию None.

        Returns:
            MangaFindResultSchema: Результат данных, с количеством страниц
        """
        return await self.service.get_pages(**common)

    async def get_pages_by_genre(
        self, request: Request, query: int, common: dict = Depends(pagination)
    ) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            query (int): ID жанра
            page (int): Номер страницы
            per_page (int, optional): Количество манги на странице. По умолчанию None.

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_genre(query, **common)

    async def get_pages_by_author(
        self, request: Request, query: int, common: dict = Depends(pagination)
    ) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            query (int): ID автора
            page (int): Номер страницы
            per_page (int, optional): Количество манги на странице. По умолчанию None.

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_author(query, **common)

    async def get_pages_by_language(
        self, request: Request, query: int, common: dict = Depends(pagination)
    ) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            query (int): ID языка
            page (int): Номер страницы
            per_page (int, optional): Количество манги на странице. По умолчанию None.

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_language(query, **common)

    async def get_pages_by_query(
        self, request: Request, query: str, common: dict = Depends(pagination)
    ) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            query (str): Текстовый запрос часть названии манги
            page (int): Номер страницы
            per_page (int, optional): Количество манги на странице. По умолчанию None.

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_query(query, **common)

    async def get_manga_by_sku(self, request: Request, sku: str) -> ApiOutputManga:
        """Получить страницу.

        Args:
            sku (str): SKU манги

        Returns:
            ApiOutputManga | None: Данные манги.
        """
        manga = await self.service.manager.get_manga_by_sku(sku)
        if manga is None:
            raise HTTPException(status_code=404, detail="Манга не найдена")

        return self._build_manga(manga)

    async def get_manga_by_url(self, request: Request, url: str) -> ApiOutputManga:
        """Получить страницу.

        Args:
            url (str): URL манги

        Returns:
            ApiOutputManga: Данные манги.
        """
        manga = await self.service.manager.get_manga_by_url(url)
        if manga is None:
            raise HTTPException(status_code=404, detail="Манга не найдена")

        return self._build_manga(manga)

    async def get_manga(self, request: Request, id: int) -> ApiOutputManga:
        """Получить страницу.

        Args:
            id (int): ID манги

        Returns:
            ApiOutputManga | None: Данные манги.
        """
        manga = await self.service.manager.get_manga(id)
        if manga is None:
            raise HTTPException(status_code=404, detail="Манга не найдена")

        return self._build_manga(manga)

    async def get_all_genres(self, request: Request) -> list[ObjectWithId]:
        """Получить все жанры

        Returns:
            list[ObjectWithId]: Обьекты с ID и названием
        """
        return await self.service.tag_getter.get_genres()

    async def get_all_languages(self, request: Request) -> list[ObjectWithId]:
        """Получить все языки

        Returns:
            list[ObjectWithId]: Обьекты с ID и названием
        """
        return await self.service.tag_getter.get_language()

    async def get_authors(
        self, request: Request, common: dict = Depends(pagination)
    ) -> list[ObjectWithId]:
        """Получить авторов постранично

        Args:
            page (int): Страница авторов
            per_page (int | None, optional): Сколько обьектов в ответе. По умолчанию None.

        Returns:
            list[ObjectWithId]: Обьекты с ID и названием
        """
        return await self.service.tag_getter.get_authors(**common)

    async def get_bot_url(self) -> str:
        """Получить URL бота."""
        return self.bot

    async def health(self):
        """Проверка работоспособности."""
        return {
            "status": "ok",
            "version": __version__,
            "service": "manga-day-api",
            "timestamp": datetime.now().isoformat(),
        }

    @property
    def router(self) -> APIRouter:
        """Получить роутер."""
        return self._router

    def _build_manga(self, manga: OutputMangaSchema) -> ApiOutputManga:
        """Создаёт мангу

        Args:
            manga (OutputMangaSchema): Манга

        Returns:
            ApiOutputManga: Манга с sku
        """
        return ApiOutputManga(
            title=manga.title,
            poster=manga.poster,
            url=manga.url,
            genres=manga.genres,
            author=manga.author,
            language=manga.language,
            gallery=manga.gallery,
            pdf_id=manga.pdf_id,
            id=manga.id,
            sku=manga.sku,
        )

    def _func_with_limit(self, func: str, limit_value: str | None = None):
        return self.limiter.limit(limit_value or f"{self.BASE_LIMIT}/minute")(func)
