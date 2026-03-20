import uvicorn

from fastapi import FastAPI

from .handlers.endpoints import Endpoints
from ..core.service import FindService
from ..core import config


def setup_api(service: FindService) -> FastAPI:
    """Инициализация API

    Args:
        service (FindService): Сервис поиска манги

    Returns:
        FastAPI: Объект FastAPI
    """
    app = FastAPI(title="Manga-Day API")

    endpoint = Endpoints(service)
    app.include_router(endpoint.router)

    return app


async def start_api(service: FindService) -> None:
    """Запускает API.

    Args:
        service (MangaManager): Сервис поиска манги
    """
    app = setup_api(service)

    _config = uvicorn.Config(
        app, host=config.api.backend_host, port=config.api.backend_port
    )

    server = uvicorn.Server(_config)
    await server.serve()
