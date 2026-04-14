from typing import Any, TypeAlias, Literal
from abc import ABC, abstractmethod

LEVEL: TypeAlias = Literal["info", "warning", "error", "critical"]


class BaseAlert(ABC):
    """
    Абстрактный класс для отправки уведомлений.
    """

    @abstractmethod
    async def alert(self, message: str, level: LEVEL) -> bool:
        """
        Отправляет уведомление.
        Args:
            message (str): Сообщение для отправки
            level (LEVEL): Уровень сообщение ["info" "warning" "error" "critical"]
        Returns:
            bool: True, если уведомление отправлено успешно, иначе False. Если
            уведомление не отправлено, то система уведомлений будет удалена
        """


class BaseMessageHandler(ABC):
    """
    Абстрактный класс для перехвата данных от WebSocket.
    """

    SIGNAL: str

    def __init_subclass__(cls):
        if not hasattr(cls, "SIGNAL"):
            raise NotImplementedError(
                f"Атрибут SIGNAL не определен в классе {cls.__name__}"
            )

    @abstractmethod
    async def __call__(self, data: Any) -> bool: ...
