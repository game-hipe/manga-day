import os

from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from ....core.service.manga import FindService


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
        self._setup_find()

    def _setup_find(self):
        self.router.add_api_route(
            "/",
            self._show_page,
            methods=["GET"],
            tags=["frontend"],
            response_class=HTMLResponse,
        )

        self.router.add_api_route(
            "/genre",
            self._show_page,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/author",
            self._show_page,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/query",
            self._show_page,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/language",
            self._show_page,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

    def _setup_routes(self):
        """Подключить эндпоинты"""
        self.router.add_api_route(
            "/static/{path:path}",
            self.get_static,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"],
        )

        self.router.add_api_route(
            "/manga/{manga_sku}",
            self._show_manga,
            tags=["frontend"],
            response_class=HTMLResponse,
            methods=["GET"],
        )

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

    def _show_page(self, request: Request) -> HTMLResponse:
        """Показать страницу

        Args:
            request (Request): Запрос от пользователя

        Returns:
            HTMLResponse: Страница от поиска.
        """

        return self.templates.TemplateResponse(
            "index.html",
            context={"request": request},
        )

    def _show_manga(
        self,
        request: Request,
    ):
        return self.templates.TemplateResponse(
            "manga.html", context={"request": request}
        )

    @property
    def router(self) -> APIRouter:
        return self._router
