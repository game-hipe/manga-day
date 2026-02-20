from aiogram import Router
from aiogram.types import Message
from aiohttp import BasicAuth

from ..core.entities.schemas import AiohttpProxy


def get_router() -> Router:
    """Роутер для обработки неизвестных команд."""
    router = Router()

    @router.message()
    async def unknown_command(message: Message):
        await message.answer(
            "Неизвестная команда. Используйте /help для получения списка доступных команд."
        )

    return router


class AiogramProxy(AiohttpProxy):
    def auth(self) -> str | tuple[str, BasicAuth]:
        proxy = super().auth()
        return (
            self.proxy
            if not proxy["proxy_auth"]
            else (proxy["proxy"], proxy["proxy_auth"])
        )
