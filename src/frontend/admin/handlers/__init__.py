from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi import Cookie
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates


STATIC = Path(__file__).parent.parent / "static"


class AdminHandler:
    def __init__(
        self,
        templates: Jinja2Templates,
        api_url: str,
        static: Path | str | None = None,
    ):
        self._router = APIRouter(prefix="/admin")

        self.static = Path(static or STATIC)
        self.templates = templates
        self.api_url = api_url

        self._setup_routers()

    def _setup_routers(self):
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
    ):
        if not access_token:
            return self.templates.TemplateResponse(
                name="login.html",
                request=request,
                context={"API": self.api_url},
            )

        else:
            response.set_cookie(key="access_token", value=access_token)
            return self.templates.TemplateResponse(
                name="index.html",
                request=request,
                context={"API": self.api_url},
            )

    async def get_static(self, path: str) -> FileResponse:
        static_file = self.static / path
        if static_file.exists():
            return FileResponse(static_file)
        raise HTTPException(status_code=404)
