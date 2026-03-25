import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
