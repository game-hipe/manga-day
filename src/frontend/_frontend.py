from pathlib import Path

import uvicorn

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from user import setup_user
from admin import setup_admin


def build_base_response(app: FastAPI, templates: Jinja2Templates):
    @app.exception_handler(404)
    async def not_found(request, exc):
        return templates.TemplateResponse(
            name="500.html", request=request, status_code=404
        )

    @app.exception_handler(500)
    async def server_error(request, exc):
        return templates.TemplateResponse(
            name="500.html", request=request, status_code=500
        )


def setup_frontend(api_url: str) -> FastAPI:
    app = FastAPI(title="Manga Day", description="Сайт для просмотра мангиг")

    shared_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

    app.include_router(setup_admin(api_url=api_url))
    app.include_router(setup_user(api_url=api_url))

    build_base_response(app, shared_templates)

    return app


async def start_frontend(frontend_host: str, frontend_port: str, api_url: str) -> None:
    app = setup_frontend(api_url)

    _config = uvicorn.Config(app, host=frontend_host, port=int(frontend_port))
    server = uvicorn.Server(_config)

    await server.serve()
