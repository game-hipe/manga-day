import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from .handlers import UserHandler

USER_FILES = Path(os.path.abspath(__file__)).parent

TEMPLATES = USER_FILES / "templates"
STATIC = USER_FILES / "static"


def setup_user(api_url: str) -> APIRouter:
    templates = Jinja2Templates(TEMPLATES)
    router = APIRouter()

    user_router = UserHandler(templates=templates, static=STATIC, api_url=api_url)

    router.include_router(user_router.router)

    return router
