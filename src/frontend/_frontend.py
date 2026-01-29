import uvicorn

from fastapi import FastAPI

from .user import setup_user
from ..core.manager.manga import MangaManager
from ..core import config


def setup_frontend(manager: MangaManager) -> FastAPI:
    app = FastAPI(title="Manga Day", description="Сайт для просмотра мангиг")

    for router in [
        # setup_admin(),
        setup_user(manager)
    ]:
        app.include_router(router)

    return app


async def start_frontend(manager: MangaManager) -> None:
    app = setup_frontend(manager)

    _config = uvicorn.Config(
        app, host="127.0.0.1", port=config.api.frontend_port, reload=True
    )
    server = uvicorn.Server(_config)

    await server.serve()
