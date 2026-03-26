from fastapi import APIRouter, HTTPException, Depends, Query

from ...core.service import FindService
from ...core.entities.schemas import (
    ApiOutputManga,
    OutputMangaSchema,
    MangaSchema,
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

    def __init__(self, service: FindService, bot: str):
        """Инициализация Endpoints

        Args:
            service (FindService): Сервис для работы с мангой.
            bot (str): URL бота Telegram.
        """
        self.service = service
        self.bot = bot
        self._router = APIRouter(prefix="/api/v1", tags=["api"])

        self._setup_routes()
        self._setup_tag_routes()
        self._setup_finder_routes()

        self._setuo_tools()

    def _setuo_tools(self):
        """Настройка инструментов."""

        self._router.add_api_route(
            "/bot",
            self.get_bot_url,
            methods=["GET"],
            response_model=str,
            summary="Получить URL бота",
            tags=["tools"],
        )

    def _setup_routes(self):
        """
        Настройка роутера добавление новых поинтов
        """
        self._router.add_api_route(
            "/manga/sku/{sku}",
            self.get_manga_by_sku,
            methods=["GET"],
            response_model=ApiOutputManga,
            summary="Получить мангу по SKU",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/url/{url}",
            self.get_manga_by_url,
            methods=["GET"],
            response_model=ApiOutputManga,
            summary="Получить мангу по URL",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/{id}",
            self.get_manga,
            methods=["GET"],
            response_model=ApiOutputManga,
            summary="Получить мангу по внутреннему ID в БД",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/manga/add",
            self.add_manga,
            methods=["POST"],
            response_model=ApiOutputManga,
            summary="Добавить мангу",
            tags=["manga"],
        )

    def _setup_finder_routes(self):
        self._router.add_api_route(
            "/pages",
            self.get_pages,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по страницам",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/genre",
            self.get_pages_by_genre,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по жанру",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/author",
            self.get_pages_by_author,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по автору",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/language",
            self.get_pages_by_language,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по языку",
            tags=["find"],
        )

        self._router.add_api_route(
            "/pages/query",
            self.get_pages_by_query,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по запросу",
            tags=["find"],
        )

    def _setup_tag_routes(self):
        self._router.add_api_route(
            "/genres",
            self.get_all_genres,
            methods=["GET"],
            response_model=list[ObjectWithId],
            summary="Получить список жанров",
            tags=["Tags"],
        )

        self._router.add_api_route(
            "/language",
            self.get_all_languages,
            methods=["GET"],
            response_model=list[ObjectWithId],
            summary="Получить список языков",
            tags=["Tags"],
        )

        self._router.add_api_route(
            "/author",
            self.get_authors,
            methods=["GET"],
            response_model=list[ObjectWithId],
            summary="Получить список авторов",
            tags=["Tags"],
        )

    async def get_pages(
        self, common: dict = Depends(pagination)
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
        self, query: int, common: dict = Depends(pagination)
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
        self, query: int, common: dict = Depends(pagination)
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
        self, query: int, common: dict = Depends(pagination)
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
        self, query: str, common: dict = Depends(pagination)
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

    async def get_manga_by_sku(self, sku: str) -> ApiOutputManga:
        """Получить страницу.

        Args:
            page (int): Номер страницы)
            sku (str):

        Returns:
            ApiOutputManga | None: Данные манги.
        """
        manga = await self.service.manager.get_manga_by_sku(sku)
        if manga is None:
            raise HTTPException(status_code=404, detail="Манга не найдена")

        return self._build_manga(manga)

    async def get_manga_by_url(self, url: str) -> ApiOutputManga:
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

    async def get_manga(self, id: int) -> ApiOutputManga:
        """Получить страницу.

        Args:
            id (int): ID манги

        Returns:
            ApiOutputManga | None: Данные манги.
        """
        manga = await self.service.manager.get_manga(id)
        if manga is None:
            raise HTTPException(status_code=404, detail="Манга не найдена")
        print(manga)
        return self._build_manga(manga)

    async def add_manga(self, manga: MangaSchema) -> ApiOutputManga:
        """Добавляет мангу в БД

        Args:
            manga (MangaSchema): Схема манги

        Returns:
            OutputMangaSchema: Возвращает мангу с ID
        """
        return self._build_manga(await self.service.manager.add_manga(manga))

    async def get_all_genres(self) -> list[ObjectWithId]:
        """Получить все жанры

        Returns:
            list[ObjectWithId]: Обьекты с ID и названием
        """
        return await self.service.tag_getter.get_genres()

    async def get_all_languages(self) -> list[ObjectWithId]:
        """Получить все языки

        Returns:
            list[ObjectWithId]: Обьекты с ID и названием
        """
        return await self.service.tag_getter.get_language()

    async def get_authors(
        self, common: dict = Depends(pagination)
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
        return self.bot

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
