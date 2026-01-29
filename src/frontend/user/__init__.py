import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from .handlers import UserRouter
from ...core.manager.manga import MangaManager

USER_FILES = Path(os.path.abspath(__file__)).parent

TEMPLATES = USER_FILES / "templates"
STATIC = USER_FILES / "static"

def setup_user(manager: MangaManager) -> APIRouter:
    router = APIRouter()
    templates = Jinja2Templates(TEMPLATES)
    user_router = UserRouter(
        manga_manager = manager,
        templates = templates,
        static = STATIC
    )
    
    router.include_router(user_router.router)
    
    return router
