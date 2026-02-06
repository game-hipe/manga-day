from ...core.abstract.alert import BaseAlert, LEVEL
from fastapi.websockets import WebSocket, WebSocketState


class AdminAlert(BaseAlert):
    def __init__(self, wb: WebSocket):
        self._wb = wb

    async def alert(self, message: str, level: LEVEL) -> bool:
        if self.is_closed():
            return False

        await self._wb.send_json({"message": message, "level": level})
        return True

    def is_closed(self):
        return self._wb.client_state == WebSocketState.DISCONNECTED
