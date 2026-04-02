import asyncio

from fastapi import Request, APIRouter, HTTPException, status, Response, Depends

from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from slowapi import Limiter
from loguru import logger

from ...core.manager import SpiderManager, AuthManager
from ...core.manager.spider import SpiderStatus
from ..schemas.spider import ParsingSignal, AuthStatus, SpiderResponse
from .._tools import auth_checker
from .._alert import AdminAlert


class SpiderEndpoints:
    """API для управление пауков."""

    def __init__(self, spider: SpiderManager, auth: AuthManager, limiter: Limiter):
        """API для управление пауков.

        Args:
            spider (SpiderManager): Менеджер пауков.
        """
        self.limiter = limiter
        self._latest = None
        self._auth = auth
        self._spider = spider
        self._api_router = APIRouter(dependencies=[Depends(auth_checker(auth))])
        self._router = APIRouter(prefix="/v1/api/admin", tags=["admin"])

        self._setup_router()
        self._router.include_router(self._api_router)

    def _setup_router(self):
        """Настроить роутер."""
        login = self.limiter.limit("3/minute")(self.login)
        self._router.add_api_route(
            "/login", login, response_model=AuthStatus, methods=["POST"]
        )

        self._api_router.add_api_route("/spider", self.spider_start, methods=["POST"])

        self._api_router.add_api_route(
            "/spider/status",
            self.spider_status,
            response_model=list[SpiderStatus],
            methods=["GET"],
        )

        self.router.add_api_websocket_route("/ws", self.spider_websocket)

    async def login(
        self, request: Request, response: Response, username: str, password: str
    ) -> AuthStatus:
        """Авторизация

        Args:
            user_name (str): Логин администратора
            password (str): пароль администратора

        Returns:
            AuthStatus: Токен авторизации
        """
        if auth_response := self._auth.login(username, password):
            response.set_cookie("access_token", auth_response["token"])
            return AuthStatus(**auth_response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Некорректные данные"
        )

    async def spider_start(self, signal: ParsingSignal) -> list[SpiderStatus]:
        """Запускает парсинг.

        Args:
            signal (ParsingSignal): Сигнал запуска.
        """
        try:
            if signal.signal == "start":
                if signal.spider == "all":
                    asyncio.create_task(self.spider.start_full_parsing())

                else:
                    asyncio.create_task(
                        self.spider.starter.start_spider(
                            spider=signal.spider, start_page=signal.page
                        )
                    )

            else:
                if signal.spider == "all":
                    await self.spider.stop_all_spider()
                else:
                    await self.spider.starter.stop_spider(spider=signal.spider)
        finally:
            await asyncio.sleep(signal.timeout)

        return self.spider.status

    async def spider_websocket(self, websocket: WebSocket):
        """Сокет для получение данных в реальном времени

        Args:
            websocket (WebSocket): Websocket соединение

        Returns:
            NoReturn: Не возвращает данные, так как работает в бесконечном цикле
        """
        await websocket.accept()
        alert = AdminAlert(websocket)
        if self.spider.alert is None:
            logger.error(
                "Не удалось подключиться к сокету, так как в менеджер пауков не был передан менеджер логирование"
            )
            await websocket.close()
            return None

        self.spider.alert.add_alert(alert)

        async def send_status():
            try:
                self._latest = self._spider_status
                await websocket.send_json(
                    SpiderResponse(
                        result=[x.as_dict() for x in self.spider.status]
                    ).model_dump()
                )
                while True:
                    if self._latest != self._spider_status:
                        await websocket.send_json(
                            SpiderResponse(
                                result=[x.as_dict() for x in self.spider.status]
                            ).model_dump()
                        )
                        self._latest = self._spider_status

                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info("Отключение системы.")

            except WebSocketDisconnect:
                logger.debug("Пользователь отключился")

            finally:
                if not websocket.client_state == WebSocketState.DISCONNECTED:
                    try:
                        await websocket.close()
                    except RuntimeError:
                        pass

        try:
            await send_status()
        except RuntimeError:
            pass
        finally:
            self.spider.alert.remove_alert(alert)

    async def spider_status(self) -> list[SpiderStatus]:
        """Возращает статус всех пауков.

        Returns:
            list[SpiderStatus]: Статус всех пауков.
        """
        return self.spider.status

    @property
    def spider(self) -> SpiderManager:
        """Менеджер пауков"""
        return self._spider

    @property
    def auth(self) -> AuthManager:
        """Менеджер авторизации"""
        return self._auth

    @property
    def router(self) -> APIRouter:
        """Роутер"""
        return self._router

    @property
    def _spider_status(self):
        return "\n".join(str(x) for x in self.spider.status)
