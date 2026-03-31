import json
from pathlib import Path

from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, HTTPException, Response, Cookie

from _dataclass import UrlParams

STATIC = Path(__file__).parent.parent / "static"


class AdminHandler:
    """Обработчик команд для административной части."""

    def __init__(
        self,
        templates: Jinja2Templates,
        url_params: UrlParams,
        static: Path | str | None = None,
    ):
        """Обработчик команд для административной части.

        Args:
            templates (Jinja2Templates): Шаблонизатор HTML.
            url_params (UrlParams): Параметры для API.
            static (Path | str | None, optional): Путь к статике. По умолчанию None.
        """
        self._router = APIRouter(prefix="/admin")

        self.static = Path(static or STATIC)
        self.templates = templates
        self.url_params = url_params

        self._setup_routers()

    def _setup_routers(self):
        """Настроить роутеры."""

        self._router.add_api_route(
            "/",
            self.index,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["admin"],
        )

        self._router.add_api_route(
            "/static/{path:path}",
            self.get_static,
            methods=["GET"],
            response_class=FileResponse,
            tags=["frontend"],
        )

    async def index(
        self,
        response: Response,
        request: Request,
        access_token: str | None = Cookie(None),
    ) -> HTMLResponse:
        """Вернуть index.html, при условии что Cookie рабочий.

        Args:
            response (Response): Результат.
            request (Request): Запрос.
            access_token (str | None, optional): Токен для входа. По умолчанию Cookie(None).

        Returns:
            HTMLResponse: Подгруженный HTML.
        """
        if not access_token:
            return self.templates.TemplateResponse(
                name="login.html",
                request=request,
                context={"API": json.dumps(self.url_params.use_rules)},
            )

        else:
            response.set_cookie(key="access_token", value=access_token)
            return self.templates.TemplateResponse(
                name="index.html",
                request=request,
                context={"API": json.dumps(self.url_params.use_rules)},
            )

    async def get_static(self, path: str) -> FileResponse:
        """Получить статику.

        Args:
            path (str): Путь к файлу.

        Raises:
            HTTPException: Если файл не найден.

        Returns:
            FileResponse: Файл.
        """
        static_file = self.static / path
        if static_file.exists():
            return FileResponse(static_file)
        raise HTTPException(status_code=404)
