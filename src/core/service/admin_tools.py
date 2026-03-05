"""Всякие особенности для админов."""

import asyncio

from typing import AsyncIterable

from ..manager.manga import MangaManager


class AdminTools:
    BASE_TIMEOUT: float = 5.0

    def __init__(self, manager: MangaManager, timeout: float | None = None):
        """Инициализирует экземпляр класса.

        Args:
            manager (MangaManager): Менеджер манги
            timeout (float | None, optional): Интервал между запросами. Обычное состояние None.
        """
        self._manager = manager
        self.timeout = timeout or self.BASE_TIMEOUT

        self._last_count: int | None = None

    async def get_count(self) -> AsyncIterable[int, None]: # TODO: Нужно это доделать, это пока прототип
        """Получает количество манги в базе данных и возращает их в реальном времени.

        Returns:
            int: Количество манги в базе данных.
        """
        try:
            if self._last_count is not None:
                yield self._last_count

            while True:
                await asyncio.sleep(self.timeout)
                count = await self.manager.get_total()
                if count != self._last_count:
                    self._last_count = count

                yield self._last_count

        except asyncio.CancelledError:
            ...

    @property
    def manager(self) -> MangaManager:
        """Менеджер манги."""
        return self._manager
