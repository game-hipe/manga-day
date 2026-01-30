import os
from pathlib import Path

import uvicorn

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from .user import setup_user
from ..core.manager.manga import MangaManager
from ..core import config


START_PATH = Path(os.path.abspath(__file__)).parent

USER_TEMPLATES = START_PATH / "user" / "templates"


def build_base_response(app: FastAPI, templates: Jinja2Templates):
    @app.exception_handler(404)
    async def not_found(request, exc):
        return templates.TemplateResponse(
            "404.html", status_code=404, context={"request": request}
        )


def setup_frontend(manager: MangaManager) -> FastAPI:
    app = FastAPI(title="Manga Day", description="Сайт для просмотра мангиг")
    templates = Jinja2Templates(USER_TEMPLATES)

    # app.include_router(
    #    setup_admin()
    # )

    app.include_router(setup_user(manager, templates))
    build_base_response(app, templates)

    return app


async def start_frontend(manager: MangaManager) -> None:
    app = setup_frontend(manager)

    _config = uvicorn.Config(app, host="0.0.0.0", port=config.api.frontend_port)
    server = uvicorn.Server(_config)

    await server.serve()
