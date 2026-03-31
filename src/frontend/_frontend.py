from pathlib import Path

import uvicorn

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from loguru import logger

from user import setup_user
from admin import setup_admin
from _dataclass import UrlParams


def build_base_response(app: FastAPI, templates: Jinja2Templates) -> None:
    """Сборка базовых ответов на ошибки 404, 500.

    Args:
        app (FastAPI): Приложение FastAPI
        templates (Jinja2Templates): Шаблоны
    """
    logger.debug("Сборка базовых ответов на ошибки 404, 500.")

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


def setup_frontend(url_params: UrlParams) -> FastAPI:
    """Настройка всего фронтенда

    Args:
        url_params (UrlParams): Параметры API

    Returns:
        FastAPI: Фронтенд
    """
    logger.info("Настройка всего фронтенда")
    app = FastAPI(title="Manga Day", description="Сайт для просмотра манги")

    shared_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

    app.include_router(setup_admin(url_params=url_params))
    app.include_router(setup_user(url_params=url_params))

    build_base_response(app, shared_templates)

    return app


async def start_frontend(
    frontend_host: str, frontend_port: str, url_params: UrlParams
) -> None:
    """Запсутить фронтенд, Uvicorn

    Args:
        frontend_host (str): Хост для фронтенда
        frontend_port (str): Порт для фронтенда
        url_params (UrlParams): Параметры API
    """

    app = setup_frontend(url_params)

    _config = uvicorn.Config(app, host=frontend_host, port=int(frontend_port))
    server = uvicorn.Server(_config)

    logger.info(f"Запуск фронтенда на {frontend_host}:{frontend_port}")
    await server.serve()
