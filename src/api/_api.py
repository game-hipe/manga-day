import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .handlers import Endpoints, SpiderEndpoints
from ..core.service import FindService
from ..core.manager import AuthManager, SpiderManager
from ..core import config, __version__


def setup_api(
    service: FindService, auth: AuthManager, spider: SpiderManager
) -> FastAPI:
    """Инициализация API

    Args:
        service (FindService): Сервис поиска манги
        auth (AuthManager): Менеджер авторизации
        spider (SpiderManager): Менеджер спайдера

    Returns:
        FastAPI: Объект FastAPI
    """
    limiter = Limiter(key_func=get_remote_address)
    app = FastAPI(title="Manga-Day API", version=__version__)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    endpoint = Endpoints(service, config.user_bot.url, limiter)
    spider_endpoint = SpiderEndpoints(spider, auth, limiter)

    app.include_router(endpoint.router)
    app.include_router(spider_endpoint.router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


async def start_api(
    service: FindService, auth: AuthManager, spider: SpiderManager
) -> None:
    """Запускает API.

    Args:
        service (MangaManager): Сервис поиска манги
    """
    app = setup_api(service, auth, spider)

    _config = uvicorn.Config(
        app, host=config.api.backend_host, port=config.api.backend_port
    )

    server = uvicorn.Server(_config)
    await server.serve()
