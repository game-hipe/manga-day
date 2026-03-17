from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import BasicAuth

from ..core.entities.schemas import AiohttpProxy


def cancel_router() -> Router:
    """Роутер для отмены действия."""
    router = Router()

    @router.message(Command("cancel"))
    async def cancel_handler(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Действие отменено.")

    return router


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
