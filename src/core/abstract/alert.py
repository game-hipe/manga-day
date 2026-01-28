from abc import ABC, abstractmethod


class BaseAlert(ABC):
    @abstractmethod
    async def alert(self, message: str) -> None: ...
