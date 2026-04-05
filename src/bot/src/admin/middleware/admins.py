from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from typing import Callable, Any, Awaitable


class AdminMiddleware(BaseMiddleware):
    """
    Мидлварь для проверки прав администратора.
    Проверяет, что пользователь является администратором.
    """

    def __init__(self, admin_ids: list[int]):
        super().__init__()
        self.admin_ids = admin_ids

        if not self.admin_ids:
            raise ValueError("Список admin_ids не должен быть пустым")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.from_user.id not in self.admin_ids:
                await event.answer(
                    f"У вас нет прав администратора!\nВаш ID: <code>{event.from_user.id}</code>"
                )
                return

        return await handler(event, data)
