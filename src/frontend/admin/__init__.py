import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from loguru import logger

from .handlers import AdminHandler
from _dataclass import UrlParams

ADMIN_FILES = Path(os.path.abspath(__file__)).parent / "templates"


def setup_admin(url_params: UrlParams) -> APIRouter:
    """Настройка административнго интерфейса.

    Args:
        url_params (UrlParams): Параметры для API.

    Returns:
        APIRouter: Роутер для административного интерфейса.
    """
    logger.debug("Настройка административнго интерфейса")
    templates = Jinja2Templates(ADMIN_FILES)
    command = AdminHandler(templates=templates, url_params=url_params)

    return command._router
