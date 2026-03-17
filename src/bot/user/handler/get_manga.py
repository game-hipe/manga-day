from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ._base import UserBaseHandler


class GetMangaCommandHandler(UserBaseHandler):
    PATH_TO_MANGA = "/manga/{sku}"
    """Путь к манге на сайте"""

    def connect(self):
        self.message_register(self.get_manga_command, Command("get_manga"))
        self.callback_register(self.get_manga_call, F.data.startswith("show:"))

    async def get_manga_call(self, call: CallbackQuery):
        try:
            command, sku = call.data.split(":", maxsplit=1)
        except ValueError:
            await call.answer("Неверный формат команды.")
            return

        await self._show_manga(call.message, sku)

    async def get_manga_command(self, message: Message):
        try:
            command, sku = message.text.split(maxsplit=1)
        except ValueError:
            await message.answer(
                "Неверный формат команды. Правильный формат: /get_manga [sku]"
            )
            return

        await self._show_manga(message, sku)

    async def _show_manga(self, message: Message, query: str):
        if manga := await self.get_manga(query):
            await self.show_manga(message=message, manga=manga, delete_message=True)
            return

        await self.manga_not_found(message)
