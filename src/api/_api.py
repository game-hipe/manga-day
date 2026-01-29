import uvicorn

from fastapi import FastAPI

from .handlers.endpoints import Endpoints
from ..core.manager.manga import MangaManager


def setup_api(manga_manager: MangaManager) -> FastAPI:
    app = FastAPI(title = "Manga-Day API")
    
    endpoint = Endpoints(manga_manager)
    app.include_router(endpoint.router)
    
    return app

async def start_api(manga_manager: MangaManager) -> None:
    app = setup_api(manga_manager)
    
    _config = uvicorn.Config(
        app, host = "127.0.0.1", port = 8000
    )
    
    server = uvicorn.Server(_config)
    await server.serve()