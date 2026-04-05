from ...core.api import AdminAPI
from ..._handler import BaseHandler
from .._bot import AdminBot


class AdminBaseHandler(BaseHandler[AdminBot]):
    """
    Административный базовый Handler
    """

    @property
    def api(self) -> AdminAPI:
        """Менеджер пауков"""
        return self.bot.api
