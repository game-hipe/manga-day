from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message


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
