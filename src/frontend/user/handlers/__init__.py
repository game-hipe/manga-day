import os

from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from ....core.manager.manga import MangaManager

USER_FILES = Path(os.path.abspath(__file__)).parent.parent


class UserRouter:
    def __init__(
        self,
        manga_manager: MangaManager,
        templates: Jinja2Templates,
        static: Path | str | None = None
    ):
        self._router = APIRouter(tags = ["user"])
        self.manga_manager = manga_manager
        self.templates = templates
        self.static = Path(static) or USER_FILES / "static"
        self._setup_routes()

    def _setup_routes(self):
        self._router.add_api_route(
            "/pages/{page}",
            self.get_pages,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"]
        )
        
        self.router.add_api_route(
            "/static/{path:path}",
            self.get_static,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["frontend"]
        )
        
        self.router.add_api_route(
            "/",
            self.get_pages,
            methods=["GET"],
            tags=["frontend"],
            response_class=HTMLResponse
        )

    async def get_pages(self, *, page: int = 1, request: Request) -> None:
        result = await self.manga_manager.get_manga_pages(page)
        if not result:
            return HTMLResponse(
                content="No pages found",
                status_code=404
            )
            
        return self.templates.TemplateResponse(
            "index.html",
            context = {
                "request": request,
                "mangas": [
                    x.as_dict() for x in result
                ]
            }
        )
        
    async def get_static(self, path: str) -> FileResponse:
        static_file = self.static / path
        if static_file.exists():
            return FileResponse(
                static_file
            )
        raise HTTPException(
            status_code=404,
            message="File not found"
        )

    @property
    def router(self) -> APIRouter:
        return self._router