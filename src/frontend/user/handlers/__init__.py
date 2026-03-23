import os

from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from ....core.entities.schemas import MangaFindResultSchema
from ....core.service.manga import FindService
from ....core import config


USER_FILES = Path(os.path.abspath(__file__)).parent.parent


class UserHandler:
    """Эндпоинты для FrontEnd"""

    def __init__(
        self,
        templates: Jinja2Templates,
        find: FindService,
        static: Path | str | None = None,
    ):
        """Эндпоинты для FrontEnd

        Args:
            templates (Jinja2Templates): Шаблонизатор
            find (FindService): Сервис поиска
            static (Path | str | None, optional): Путь к статике. По умолчанию None.
        """
        self._router = APIRouter(tags=["user"])
        self.find_engine = find
        self.templates = templates
        self.static = Path(static) or USER_FILES / "static"
        self._setup_routes()

    def _setup_routes(self):
        """Подключить эндпоинты"""

        self._router.add_api_route(
            "/pages/{page}",
            self.get_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/static/{path:path}",
            self.get_static,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/",
            self.get_pages,
            methods=["GET"],
            tags=["frontend"],
            response_class=HTMLResponse,
        )

        self.router.add_api_route(
            "/manga/{manga_sku}",
            self.get_manga,
            tags=["frontend"],
            response_class=HTMLResponse,
            methods=["GET"],
        )

        self.router.add_api_route(
            "/manga/tags/{genre_id}",
            self.get_genres_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/manga/author/{author_id}",
            self.get_author_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/manga/language/{language_id}",
            self.get_language_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/manga/find/{query}",
            self.get_query_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

    async def get_pages(self, *, page: int = 1, request: Request) -> HTMLResponse:
        """Получить страницу от поиска.

        Args:
            request (Request): Запрос от клиента.
            page (int, optional): Страница. По умолчанию 1.

        Returns:
            HTMLResponse: Страница от поиска
        """
        result = await self.find_engine.get_pages(page)
        self._bad_response(result)
        return self._show_page(result, request)

    async def get_manga(self, *, manga_sku: str, request: Request) -> HTMLResponse:
        """Получить страницу с мангой

        Args:
            manga_sku (str): артикул манги
            request (Request): запрос от клиента

        Returns:
            HTMLResponse: Страница с мангой
        """
        manga = await self.find_engine.manager.get_manga_by_sku(sku=manga_sku)

        if manga is None:
            return self.templates.TemplateResponse(
                "404.html", status_code=404, context={"request": request}
            )

        return self.templates.TemplateResponse(
            "manga.html",
            context={
                "request": request,
                "manga": manga.as_dict(),
                "bot": config.user_bot.url,
            },
        )

    async def get_genres_pages(
        self, *, genre_id: int, page: int = 1, request: Request
    ) -> HTMLResponse:
        """Получить страницу от поиска.

        Args:
            genre_id (int): ID жанра
            request (Request): Запрос от клиента.
            page (int, optional): Страница. По умолчанию 1.

        Returns:
            HTMLResponse: Страница от поиска
        """
        result = await self.find_engine.get_pages_by_genre(genre_id, page)
        self._bad_response(result)

        title = await self.find_engine.tag_getter.get(genre_id, "genre")

        return self._show_page(result, request, title=f"[Жанр]: {title}")

    async def get_author_pages(
        self, *, author_id: int, page: int = 1, request: Request
    ) -> HTMLResponse:
        """Получить страницу от поиска.

        Args:
            author_id (int): ID автора
            request (Request): Запрос от клиента.
            page (int, optional): Страница. По умолчанию 1.

        Returns:
            HTMLResponse: Страница от поиска
        """
        result = await self.find_engine.get_pages_by_author(author_id, page)
        self._bad_response(result)

        title = await self.find_engine.tag_getter.get(author_id, "author")

        return self._show_page(result, request, title=f"[Автор]: {title}")

    async def get_language_pages(
        self, *, language_id: int, page: int = 1, request: Request
    ) -> HTMLResponse:
        """Получить страницу от поиска.

        Args:
            language_id (int): ID языка
            request (Request): Запрос от клиента.
            page (int, optional): Страница. По умолчанию 1.

        Returns:
            HTMLResponse: Страница от поиска
        """
        result = await self.find_engine.get_pages_by_language(language_id, page)
        self._bad_response(result)

        title = await self.find_engine.tag_getter.get(language_id, "language")

        return self._show_page(result, request, title=f"[Язык]: {title}")

    async def get_query_pages(
        self, *, query: str, page: int = 1, request: Request
    ) -> HTMLResponse:
        """Получить страницу от поиска.

        Args:
            query (int): Запрос
            request (Request): Запрос от клиента.
            page (int, optional): Страница. По умолчанию 1.

        Returns:
            HTMLResponse: Страница от поиска
        """
        result = await self.find_engine.get_pages_by_query(query, page)
        if not result.response:
            return await self.get_manga(manga_sku=query, request=request)

        return self._show_page(result, request, title=f"[Запрос]: {query}")

    async def get_static(self, path: str) -> FileResponse:
        """Получить статичный файл

        Args:
            path (str): Путь ка файлу

        Raises:
            HTTPException: Если файл не найден

        Returns:
            FileResponse: Файл
        """
        static_file = self.static / path
        if static_file.exists():
            return FileResponse(static_file)
        raise HTTPException(status_code=404)

    def _bad_response(self, result: MangaFindResultSchema) -> None:
        """Проверяет на то удачный ли результат поиска

        Args:
            result (MangaFindResultSchema): Результат поиска
        """
        if not result.response:
            return self._show_404()

        if not result.succsess:
            return self._show_500()

    def _show_404(self):
        """Страница 404"""
        raise HTTPException(status_code=404)

    def _show_500(self):
        """Страница 500"""
        raise HTTPException(status_code=500)

    def _show_page(
        self, result: MangaFindResultSchema, request: Request, title: str | None = None
    ) -> HTMLResponse:
        """Показать страницу

        Args:
            result (MangaFindResultSchema): Результат поиска
            request (Request): Запрос от пользователя
            title (str | None, optional): Описание страницы. По умолчанию None.

        Returns:
            HTMLResponse: Страница от поиска.
        """

        return self.templates.TemplateResponse(
            "index.html",
            context={
                "request": request,
                "mangas": [x.as_dict() for x in result.response],
                "total": result.page,
                "page_now": result.page_now,
                "title": (title or "Manga-Day") + f" найдено манги {result.total}",
            },
        )

    @property
    def router(self) -> APIRouter:
        return self._router
