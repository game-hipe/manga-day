from ....core.manager import SpiderManager
from ..._handler import BaseHandler
from .._bot import AdminBot


class AdminBaseHandler(BaseHandler[AdminBot]):
    """
    Административный базовый Handler
    """

    @property
    def spider(self) -> SpiderManager:
        """Менеджер пауков"""
        return self.bot.spider
