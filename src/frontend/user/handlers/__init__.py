import os
import json

from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from _dataclass import UrlParams

STATIC = Path(os.path.abspath(__file__)).parent.parent / "static"


class UserHandler:
    """Эндпоинты для FrontEnd"""

    def __init__(
        self,
        templates: Jinja2Templates,
        url_params: UrlParams,
        static: Path | str | None = None,
    ):
        """Эндпоинты для FrontEnd

        Args:
            templates (Jinja2Templates): Шаблонизатор
            url_params (UrlParams): Параметры для API.
            static (Path | str | None, optional): Путь к статике. По умолчанию None.
        """
        self._router = APIRouter(tags=["user"])
        self.templates = templates
        self.static = Path(static or STATIC)
        self.url_params = url_params
        self._setup_routes()
        self._setup_find()

    def _setup_find(self):
        """Подключить эндпоинты"""
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

        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def health(self):
        """Проверка работоспособности"""
        return {"ok": True}

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

    async def _show_page(self, request: Request) -> HTMLResponse:
        """Показать страницу

        Args:
            request (Request): Запрос от пользователя

        Returns:
            HTMLResponse: Страница от поиска.
        """

        return self.templates.TemplateResponse(
            name="index.html",
            request=request,
            context={"API": json.dumps(self.url_params.use_rules)},
        )

    async def _show_manga(
        self,
        request: Request,
    ) -> HTMLResponse:
        """Показать мангу

        Args:
            request (Request): Запрос от пользователя

        Returns:
            HTMLResponse: Страница манги
        """
        return self.templates.TemplateResponse(
            name="manga.html",
            request=request,
            context={"API": json.dumps(self.url_params.use_rules)},
        )

    @property
    def router(self) -> APIRouter:
        return self._router
