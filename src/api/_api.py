import uvicorn

from fastapi import FastAPI

from .handlers.endpoints import Endpoints
from ..core.manager.manga import MangaManager
from ..core import config


def setup_api(manager: MangaManager) -> FastAPI:
    app = FastAPI(title="Manga-Day API")

    endpoint = Endpoints(manager)
    app.include_router(endpoint.router)

    return app


async def start_api(manager: MangaManager) -> None:
    app = setup_api(manager)

    _config = uvicorn.Config(app, host="0.0.0.0", port=config.api.backend_port)

    server = uvicorn.Server(_config)
    await server.serve()
