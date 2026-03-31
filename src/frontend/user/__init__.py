import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from loguru import logger

from .handlers import UserHandler
from _dataclass import UrlParams

USER_FILES = Path(os.path.abspath(__file__)).parent

TEMPLATES = USER_FILES / "templates"


def setup_user(url_params: UrlParams) -> APIRouter:
    """Настройка пользователского интерфейса.

    Args:
        url_params (UrlParams): Параметры для API.

    Returns:
        APIRouter: Роутер для пользователского интерфейса.
    """
    logger.debug("Настройка пользователского интерфейса.")
    templates = Jinja2Templates(TEMPLATES)

    user_router = UserHandler(templates=templates, url_params=url_params)

    return user_router.router
