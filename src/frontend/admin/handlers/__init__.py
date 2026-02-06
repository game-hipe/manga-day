import asyncio

from pathlib import Path

from loguru import logger
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketDisconnect

from ....core import config
from ....core.manager import MangaManager, SpiderManager
from .._alert import AdminAlert


STATIC = Path(__file__).parent.parent / "static"


class AdminHandler:
    def __init__(
        self,
        manager: MangaManager,
        spider: SpiderManager,
        templates: Jinja2Templates,
        static: Path | str | None = None,
    ):
        self._latest = None
        self._router = APIRouter(prefix="/admin")
        self.spider = manager
        self.spider = spider

        self.static = Path(static or STATIC)
        self.templates = templates

        self._setup_routers()

    def _setup_routers(self):
        self.router.add_api_route(
            "/",
            self.index,
            methods=["GET"],
            response_class=HTMLResponse,
            tags=["admin"],
        )

        self.router.add_api_route(
            "/static/{path:path}",
            self.get_static,
            methods=["GET"],
            response_class=FileResponse,
            tags=["frontend"],
        )

        self.router.add_api_websocket_route("/ws", self.websocket)

        self.router.add_api_websocket_route("/ws/status", self.status_socket)

    async def index(self, request: Request):
        return self.templates.TemplateResponse(
            "index.html", context={"request": request, "port": config.api.frontend_port}
        )

    async def status_socket(self, websocket: WebSocket):
        await websocket.accept()

        async def send_status():
            try:
                while True:
                    if self._latest != self.spider.status:
                        await websocket.send_text(self.spider.status)
                        self._latest = self.spider.status

                    await asyncio.sleep(0.1)

            except WebSocketDisconnect:
                logger.debug("Пользователь отключился")

        await send_status()

    async def websocket(self, websocket: WebSocket):
        await websocket.accept()
        try:
            alert = AdminAlert(websocket)
            self.spider.add_alert(alert)

            while True:
                command = await websocket.receive_text()

                if command.startswith("start"):
                    if self.spider._start:
                        await alert.alert("Парсер уже запущен!", "warning")
                        continue

                    asyncio.create_task(self.spider.start_parsing())

                elif command.startswith("stop"):
                    if not self.spider._start:
                        await alert.alert("Парсер уже остановлен!", "warning")
                        continue

                    asyncio.create_task(self.spider.stop_parsing())

                else:
                    await self.spider.alert("Внимания Неизвестная команда!", "warning")

        except (WebSocketDisconnect, RuntimeError):
            logger.debug("Пользователь отключился")

        finally:
            try:
                self.spider.alert_manager.remove_alert(alert)
            except ValueError:
                logger.debug("Уведомление было удалено сборщиком")

    async def get_static(self, path: str) -> FileResponse:
        static_file = self.static / path
        if static_file.exists():
            return FileResponse(static_file)
        raise HTTPException(status_code=404)

    @property
    def router(self) -> APIRouter:
        return self._router
