from fastapi import FastAPI

from .admin import setup_admin
from .user import setup_user


def setup_frontend() -> FastAPI:
    app = FastAPI(
        title="Manga Day",
        description="Сайт для просмотра мангиг"
    )
    
    for router in [setup_admin(), setup_user()]:
        app.include_router(router)
    
    return app