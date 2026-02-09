import asyncio
import importlib

from typing import Unpack, overload

import aiohttp

from loguru import logger

from ..abstract.spider import BaseSpider
from ..abstract.alert import BaseAlert, LEVEL
from .request import RequestManager, RequestItem
from .manga import MangaManager
from .alert import AlertManager


class SpiderManager:
    @overload
    def __init__(
        self,
        session: RequestManager,
        manager: MangaManager,
        alert: AlertManager,
        features: str | None = None,
        batch: int | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        session: aiohttp.ClientSession,
        manager: MangaManager,
        alert: AlertManager,
        features: str | None = None,
        batch: int | None = None,
        **kwargs: Unpack[RequestItem],
    ) -> None: ...

    def __init__(
        self,
        session: aiohttp.ClientSession | RequestManager,
        manager: MangaManager,
        alert: AlertManager,
        features: str = None,
        batch: int = None,
        **kwargs,
    ):
        self._total: int = 0
        self._start: bool = False
        self._manager = manager
        self.tasks: list[asyncio.Task[None]] = []
        self.spider_tasks: dict[asyncio.Task, BaseSpider] = {}
        self._alert_manager = alert

        self.spiders: list[BaseSpider] = []
        spider_module = importlib.import_module("...spider", package=__package__)

        if hasattr(spider_module, "__all__"):
            for spider in spider_module.__all__:
                try:
                    spider_factory: type[BaseSpider] = getattr(spider_module, spider)
                    if hasattr(spider_factory, "HAS_CLOUDFARE"):
                        if getattr(spider_factory, "HAS_CLOUDFARE"):
                            logger.warning(f"Парсер {spider} использует CloudFare. Парсер будет пропущен при инцилизации")
                            continue
                            
                    self.spiders.append(
                        spider_factory(
                            session=session,
                            manager=manager,
                            features=features,
                            batch=batch,
                            **kwargs,
                        )
                    )
                except ImportError:
                    logger.error(f"Ошибка при импорте класс {spider}")

                except AttributeError:
                    logger.error(f"Не удалось получить класс {spider}")

        else:
            logger.error(
                "Не удалось загрузить список доступных парсеров. Пожалуйста, проверьте наличие файла __all__ в модуле spider."
            )
            raise ImportError(
                "Не удалось загрузить список доступных парсеров. Пожалуйста, проверьте наличие файла __all__ в модуле spider."
            )

        if not self.spiders:
            raise ValueError(
                "Не удалось загрузить ни одного парсера. Пожалуйста, проверьте наличие классов в модуле spider."
            )

        logger.debug(
            f"Загружено {len(self.spiders)} парсеров: {', '.join(spider.__class__.__name__ for spider in self.spiders)}"
        )

    async def start_parsing(self):
        """
        Функция что-бы начать парсинг у всех в пауков.
        """
        if self._start:
            logger.info("Парсинг уже начат")
            await self.alert("Парсинг уже начат")
            return

        self._total = await self._manager.get_total()

        logger.info("Начало парсинга")
        await self.alert("Начало парсинга")

        for spider in self.spiders:
            task = asyncio.create_task(self._run_parser(spider))
            self.spider_tasks[task] = spider
            self.tasks.append(task)

        try:
            self._start = True
            await asyncio.shield(asyncio.gather(*self.tasks, return_exceptions=True))

            logger.info("Все парсеры завершили работу.")
            await self.alert("Все парсеры завершили работу.")

        except (asyncio.CancelledError, asyncio.CancelledError):
            await self.alert("Принудительное завершение работы...")

            await asyncio.sleep(1)

            for task in self.tasks:
                if not task.done():
                    task.cancel()

            await asyncio.gather(*self.tasks, return_exceptions=True)
            await self.alert("Парсинг прерван.")

        finally:
            result = await self._manager.get_total()

            if result != self._total:
                await self.alert(
                    f"Парсинг завершен. Найдено {result - self._total} манги. Парсинг завершен."
                )

            self.tasks.clear()
            self.spider_tasks.clear()
            self._start = False

    async def stop_parsing(self, timeout: float = 10.0):
        """Остановка с таймаутом"""
        self._start = False
        logger.info("Остановка парсинга")
        await self.alert("Остановка парсинга...")

        if not self.tasks:
            await self.alert("Нет активных задач")
            logger.info("Нет активных задач")
            return

        tasks_to_cancel = [t for t in self.tasks if not t.done()]

        if not tasks_to_cancel:
            logger.info("Все задачи уже завершены")

            self.tasks.clear()
            self.spider_tasks.clear()

            await self.alert("Парсинг уже завершен")
            return

        logger.info(f"Отменяем {len(tasks_to_cancel)} задач")

        for task in tasks_to_cancel:
            task.cancel()

        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                timeout=timeout,
            )
            logger.info("Все задачи корректно завершены")
        except asyncio.TimeoutError:
            logger.warning(f"Не все задачи завершились за {timeout} сек")
            for task in tasks_to_cancel:
                if not task.done():
                    logger.warning(f"Задача {task.get_name()} не завершилась")
        except Exception as e:
            logger.error(f"Ошибка при остановке: {e}")

        finally:
            result = await self._manager.get_total()

            if result != self._total:
                await self.alert(
                    f"Парсинг завершен. Найдено {result - self._total} манги. Парсинг завершен."
                )

            self.tasks.clear()
            self.spider_tasks.clear()

        logger.info("Парсинг остановлен")
        await self.alert("Парсинг остановлен")

    async def _run_parser(self, spider: BaseSpider) -> None:
        """Запуска парсера"""
        try:
            await spider.run()

        except Exception as e:
            logger.error(
                f"Ошибка при запуске/работе парсера {spider.__class__.__name__} (Тип ошибки: {type(e).__name__}, Ошибка: {e})"
            )
            await self.alert(
                f"Ошибка при запуске/работе парсера {spider.__class__.__name__} (Тип ошибки: {type(e).__name__}, Ошибка: {e})"
            )

        finally:
            logger.info(f"Парсер завершил работу {spider.__class__.__name__}")
            await self.alert(f"Парсер завершил работу {spider.__class__.__name__}")

    async def alert(self, message: str, level: LEVEL | None = None) -> None:
        await self._alert_manager.alert(message=message, level=level or "info")

    def add_alert(self, alert: BaseAlert) -> None:
        """Добавить уведомление."""
        self._alert_manager.add_alert(alert)

    @property
    def status(self) -> str:
        """
        Возвращает читаемый статус всех запущенных парсеров (spider'ов).

        Формат вывода:
            <Имя Spider> — Статус: <Состояние корутины> [— Доп. статус/прогресс]

        Примеры:
            MangaSpider — Статус: В работе — Парсинг глав: 45/100
            AnimeSpider — Статус: Завершён — 100%
            OldSpider   — Статус: Отменён

        Returns:
            str: Отформатированный текстовый статус всех задач.
        """
        if not self.tasks:
            return "Парсинг не запущен"

        status_lines = []
        max_spider_name_len = max(
            (
                len(self.spider_tasks.get(task).__class__.__name__)
                for task in self.tasks
                if self.spider_tasks.get(task)
            ),
            default=10,
        )

        for task in self.tasks:
            spider = self.spider_tasks.get(task)
            spider_name = getattr(spider, "__class__", None)
            spider_name = spider_name.__name__ if spider_name else "Неизвестно"

            if task.cancelled():
                coro_status = "Отменён"
                extra = ""
            elif task.done():
                if task.exception():
                    coro_status = "Ошибка"
                    extra = f" — {type(task.exception()).__name__}: {task.exception()}"
                else:
                    coro_status = "Завершён"
                    extra = " — 100%"
            else:
                coro_status = "В работе"
                extra = (
                    f" — {spider.status}"
                    if hasattr(spider, "status") and spider.status
                    else ""
                )

            padded_name = spider_name.ljust(max_spider_name_len)

            status_lines.append(
                f"<b>{padded_name}</b> — Статус: <b>{coro_status}</b>{extra}"
            )

        return "\n".join(status_lines)

    @property
    def alert_manager(self) -> AlertManager:
        """Возвращает менеджер уведомлений."""
        return self._alert_manager
