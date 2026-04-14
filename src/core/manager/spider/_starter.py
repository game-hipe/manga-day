"""Включение/выключение пауков"""

import asyncio


from bs4 import FeatureNotFound

from loguru import logger

from ..alert import AlertManager, LEVEL
from ...abstract.spider import BaseSpider


class SpiderStarter:
    def __init__(self, spiders: list[BaseSpider], alert: AlertManager | None = None):
        """Инициализация системы старта пауков.

        Args:
            spiders (list[BaseSpider]): Пауки которых можно запустить
            alert (AlertManager | None, optional): Менеджер оповещений. Обычное состояние None
        """
        self.alert = alert
        self.spiders: dict[BaseSpider, None | asyncio.Task[None]] = {
            spider: None for spider in spiders
        }

    async def stop_spider(self, spider: str | BaseSpider | type[BaseSpider]) -> None:
        """Остановить работу паука

        Args:
            spider (str | BaseSpider): Паук, либо название паука.
        """
        spider = self._get_spider(spider)

        if not self.spiders[spider]:
            await self._alert(
                f"Паук {self._get_spider_name(spider)} не запущен. Необходимо запустить его перед остановкой.",
                "warning",
            )
            return

        try:
            if task := self.spiders[spider]:
                if not task.done():
                    task.cancel()

                    await self._alert(
                        f"Паук {self._get_spider_name(spider)}, был остановлен.",
                        "warning",
                    )
                else:
                    await self._alert(
                        f"Паук {self._get_spider_name(spider)}, уже остановлен.",
                        "warning",
                    )

            else:
                await self._alert(
                    f"Паук {self._get_spider_name(spider)} не запущен.", "warning"
                )
        finally:
            self.spiders[spider] = None

    async def start_spider(
        self, spider: str | BaseSpider | type[BaseSpider], start_page: int | None = None
    ) -> None:
        """Начать работу паука.

        Args:
            spider (str | BaseSpider): Паук, либо название паука.
            start_page (int | None, optional): Параметр для выбора страницы для начало. Обычное состояние None
        """
        await self._start_spider(
            spider,
            method="run",
            start_page=start_page,
        )

    async def update_spider(
        self, spider: str | BaseSpider | type[BaseSpider], start_page: int | None = None
    ) -> None:
        """Начинает полное сканировение

        Начинает полное сканировение и обновляя данные паука.

        Если паук запущен, то он остановится.

        Args:
            spider (str | BaseSpider | type[BaseSpider]): Паук, либо название паука.
            stop_spider (bool, optional): Остановить паука если он запущен. Обычное состояние True
        """
        await self._start_spider(
            spider,
            method="update",
            start_page=start_page,
        )

    async def _start_spider(
        self,
        spider: str | BaseSpider | type[BaseSpider],
        method: str,
        start_page: int | None = None,
    ) -> None:
        """Внутренняя функция для запуска пауков

        Args:
            spider (str | BaseSpider | type[BaseSpider]): Паук, либо название паука.
            method (str): Метод запуска паука. Пример `run`, `update`
            start_page (int | None, optional): Параметр для выбора страницы для начало. Обычное состояние None
        """
        spider = self._get_spider(spider)
        if not hasattr(spider, method):
            raise AttributeError(
                f"У паука {self._get_spider_name(spider)} нет метода {method}"
            )

        if self.spiders[spider]:
            if method == "run":
                await self._alert(
                    f"Паук {self._get_spider_name(spider)} уже запущен. Необходимо остановить его перед запуском.",
                    "warning",
                )
                return

            elif method == "update":
                await self.stop_spider(spider)

        try:
            await self._alert(
                f"Паук {self._get_spider_name(spider)}, начал свою работу.", "info"
            )
            self.spiders[spider] = asyncio.create_task(
                getattr(spider, method)(start_page=start_page)
            )
            await self.spiders[spider]

        except FeatureNotFound:
            await self._alert(
                "Невозможно загрузить парсер так-как движок для парсинга не загружен",
                "error",
            )

        except (KeyboardInterrupt, asyncio.CancelledError):
            await self._alert(
                f"Паук {self._get_spider_name(spider)}, был остановлен пользователем.",
                "warning",
            )

        finally:
            if task := self.spiders[spider]:
                if not task.done():
                    task.cancel()

            self.spiders[spider] = None
            await self._alert(
                f"Паук {self._get_spider_name(spider)}, закончил свою работу.",
                "info",
            )

    def _get_spider(self, spider: str | BaseSpider | type[BaseSpider]) -> BaseSpider:
        """Получает паука по название, либо самого паука.

        Args:
            spider (str | BaseSpider): Паук, либо его название

        Raises:
            ValueError: Если паук не найден
            TypeError: Если передан не поддерживаемый тип данных

        Returns:
            BaseSpider: Паук
        """
        if isinstance(spider, BaseSpider):
            return spider
        elif isinstance(spider, str):
            for _spider in self.spiders:
                if self._get_spider_name(_spider) == spider:
                    return _spider
            else:
                logger.error(f"Паук '{spider}' не существует")
                raise KeyError(f"Паук '{spider}' не существует")
        if issubclass(spider, BaseSpider):
            for _spider in self.spiders:
                if type(_spider) is spider:
                    return _spider
            else:
                logger.error(f"Паук '{spider}' не существует")
                raise KeyError(f"Паук '{spider}' не существует")
        else:
            raise TypeError(
                f"Паук должен быть либо BaseSpider, либо str, а не {type(spider)}"
            )

    def _get_spider_name(self, spider: BaseSpider) -> str:
        return spider.__class__.__name__

    async def _alert(self, message: str, level: LEVEL):
        """
        Вспомогательная функция что-бы делать оповещении.
        При отсутствии менеджера alert не будет выброшен

        Args:
            message (str): Сообщение
            level (LEVEL): Уровень сообщение
        """
        logger.log(level.upper(), message)
        if self.alert:
            await self.alert.alert(message=message, level=level)
        else:
            logger.debug("Менеджер сообщение не передан.")

    @property
    def all_work(self) -> bool:
        return any(self.spiders.values())
