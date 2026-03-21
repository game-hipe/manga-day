from fastapi import APIRouter, HTTPException

from ...core.service import FindService
from ...core.entities.schemas import (
    ApiOutputManga,
    OutputMangaSchema,
    MangaSchema,
    MangaFindResultSchema,
)


class Endpoints:
    """Эндпоинты для API манги."""

    def __init__(self, service: FindService):
        """Инициализация Endpoints

        Args:
            service (FindService): Сервис для работы с мангой.
        """
        self.service = service
        self._router = APIRouter(prefix="/api/v1", tags=["api"])

        self._setup_routes()

    def _setup_routes(self):
        """
        Настройка роутера добавление новых поинтов
        """
        self._router.add_api_route(
            "/pages/{page}",
            self.get_pages,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по страницам",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/pages/genre/{genre_id}",
            self.get_pages_by_genre,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по жанру",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/pages/author/{author_id}",
            self.get_pages_by_author,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по автору",
            tags=["manga"],
        )

        self._router.add_api_route(
            "/pages/query/{query}",
            self.get_pages_by_query,
            methods=["GET"],
            response_model=MangaFindResultSchema,
            summary="Получить список манги по запросу",
            tags=["manga"],
        )

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

    async def get_pages(self, page: int) -> MangaFindResultSchema:
        """Получить страницу.

        Args:
            page (int): Номер страницы

        Returns:
            MangaFindResultSchema: Результат данных, с количеством страниц
        """
        return await self.service.get_pages(page)

    async def get_pages_by_genre(self, genre_id: int) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            genre_id (int): ID жанра

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_genre(genre_id)

    async def get_pages_by_author(self, author_id: int) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            author_id (int): ID автора

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_author(author_id)

    async def get_pages_by_language(self, language_id: int) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            language_id (int): ID языка

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_language(language_id)

    async def get_pages_by_query(self, query: str) -> MangaFindResultSchema:
        """Ищет мангу по запросу

        Args:
            query (str): Запрос

        Returns:
            MangaFindResultSchema: Результат поиска
        """
        return await self.service.get_pages_by_query(query)

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
