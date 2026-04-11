import asyncio
import random

from loguru import logger
import aiohttp

from .abstract.alert import BaseAlert, LEVEL
from .api import AdminAPI


class ApiWrapper:
    def __init__(self, api: AdminAPI):
        self._api = api

    async def alert(self, message: str, level: LEVEL) -> bool:
        await self._api.alert(message, level)
        return True


class AlertManager:
    def __init__(self, api: AdminAPI, ws_url: str, *alert: BaseAlert):
        self.__api = api
        self._alerts: list[BaseAlert] = [ApiWrapper(self.__api)]
        self._alerts.extend(alert)

        self.ws_url = ws_url

    async def alert(self, message: str, level: LEVEL, my_alert: bool = True) -> None:
        """Отправить уведомление всем обработчикам

        Args:
            message (str): Сообщение
            level (LEVEL): Уровень сообщение, подробнее в LEVEL
            my_alert (bool, optional): Отправить сообщение самому себе. По умолчанию True.

        Warning:
            Если event-loop закрыт, то уведомление не будет отправлено и будет выведено предупреждение в лог
            Так-же если при отправки уведомления возникла ошибка, то обработчик будет удален из списка и будет выведено сообщение об ошибке в лог
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            logger.info("Невозможно отправить Alert, even-loop закрыт")
            return

        async def _send(message: str, alert_engine: BaseAlert) -> None:
            try:
                result = await alert_engine.alert(message, level)
                if not result:
                    self._alerts.remove(alert_engine)
                    logger.debug(
                        f"Система уведомлений {type(alert_engine).__name__} было удалено"
                    )

            except Exception as e:
                self._alerts.remove(alert_engine)
                logger.error(
                    f"Ошибка при отправке уведомления {alert_engine.__class__.__name__}: {e}"
                )

        await asyncio.gather(
            *[
                _send(message, alert)
                for alert in self._alerts
                if isinstance(alert, BaseAlert) or my_alert
            ]
        )

    async def api_alert(self, message: str, level: LEVEL):
        await self.api.alert(message, level)
        return True

    async def start_listening(self) -> None:
        async with aiohttp.ClientSession() as session:
            backoff = 1.0  # начальная задержка в секундах
            max_backoff = 60.0

            while True:
                try:
                    async with session.ws_connect(self.ws_url) as ws:
                        backoff = 1.0
                        async for msg in ws:
                            try:
                                data = msg.json()
                            except Exception as e:
                                logger.error(f"Ошибка парсинга JSON: {e}")
                                continue

                            if data.get("signal") == "alert":
                                alert_data = data.get("result", {})
                                asyncio.create_task(
                                    self.alert(
                                        alert_data.get("message", ""),
                                        alert_data.get("level", "info"),
                                        my_alert=False,
                                    )
                                )
                except (
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    ConnectionError,
                ) as e:
                    logger.warning(
                        f"Потеряно соединение: {e}. Переподключение через {backoff:.2f} сек."
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 1.5 + random.uniform(0, 1), max_backoff)

                except Exception as e:
                    logger.exception(f"Неожиданная ошибка в цикле WebSocket: {e}")
                    await asyncio.sleep(5)

    def add_alert(self, alert: BaseAlert) -> None:
        """Добавить новый обработчик сообщений

        Args:
            alert (BaseAlert): Обработчик сообщений, который должен быть наследником BaseAlert

        Raises:
            TypeError: Если alert не является наследником BaseAlert
        """
        if not isinstance(alert, BaseAlert):
            logger.warning(
                "Не удалось добавить обработчик так-как он не наследуется от BaseAlert"
            )
            raise TypeError("Обработчик уведомлений должен быть наследником BaseAlert")

        if alert not in self._alerts:
            self._alerts.append(alert)
            logger.debug(
                f"Добавлен новый обработчик уведомлений: {alert.__class__.__name__}"
            )
        else:
            logger.debug(
                f"Обработчик уведомлений {alert.__class__.__name__} уже существует"
            )

    def remove_alert(self, alert: BaseAlert) -> None:
        """Удаляет обработчик сообщений из списка

        Args:
            alert (BaseAlert): Обработчик сообщений, который должен быть наследником BaseAlert
        """
        if alert in self._alerts:
            self._alerts.remove(alert)
            logger.debug(
                f"Обработчик уведомлений {alert.__class__.__name__} был удален"
            )
        else:
            logger.warning(
                f"Обработчик уведомлений {alert.__class__.__name__} не найден"
            )

    @property
    def alerts(self) -> list[BaseAlert]:
        """Список уведомлений."""
        return self._alerts.copy()

    @property
    def api(self) -> AdminAPI:
        return self.__api
