from ...core.abstract.alert import BaseAlert
from fastapi.websockets import WebSocket, WebSocketState


class AdminAlert(BaseAlert):
    def __init__(self, wb: WebSocket):
        self._wb = wb

    async def alert(self, message: str) -> bool:
        if not self.is_open():
            return False

        await self._wb.send_text(message)
        return True

    def is_open(self):
        return self._wb.client_state == WebSocketState.CONNECTED
