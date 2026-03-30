import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from .handlers import AdminHandler

ADMIN_FILES = Path(os.path.abspath(__file__)).parent / "templates"


def setup_admin(api_url: str) -> APIRouter:
    templates = Jinja2Templates(ADMIN_FILES)
    command = AdminHandler(templates=templates, api_url=api_url)

    return command._router
