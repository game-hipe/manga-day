from abc import ABC, abstractmethod


class BaseAlert(ABC):
    """
    Абстрактный класс для отправки уведомлений.
    """

    @abstractmethod
    async def alert(self, message: str) -> None:
        """Отправляет уведомление."""
