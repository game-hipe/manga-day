from abc import ABC, abstractmethod


class BaseAlert(ABC):
    """
    Абстрактный класс для отправки уведомлений.
    """

    @abstractmethod
    async def alert(self, message: str) -> bool:
        """
        Отправляет уведомление.
        
        Returns:
            bool: True, если уведомление отправлено успешно, иначе False. Если 
            уведомление не отправлено, то система алёртов будет удалена
        """
