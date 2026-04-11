from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ._base import UserBaseHandler


class MangaStates(StatesGroup):
    browsing = State()


class GetMangaCommandHandler(UserBaseHandler):
    PATH_TO_MANGA = "/manga/{sku}"
    """Путь к манге на сайте"""

    def connect(self):
        self.message_register(self.get_manga_command, Command("get"))
        self.message_register(self.get_random_manga, Command("random"))
        self.message_register(self.get_manga_user, MangaStates.browsing, F.text)
        self.callback_register(self.get_manga_call, F.data.startswith("show:"))

    async def get_manga_call(self, call: CallbackQuery, state: FSMContext):
        try:
            command, sku = call.data.split(":", maxsplit=1)
        except ValueError:
            await call.answer("Неверный формат команды.")
            return

        await self._show_manga(call.message, sku, state)

    async def get_manga_command(self, message: Message, state: FSMContext):
        try:
            command, sku = message.text.split(maxsplit=1)
        except ValueError:
            await message.answer("Введите URL, либо артикул манги: ")
            await state.set_state(MangaStates.browsing)
            return

        await self._show_manga(message, sku, state)

    async def get_manga_user(self, message: Message, state: FSMContext):
        try:
            await self._show_manga(message, message.text, state)
        finally:
            await state.set_state(state=None)

    async def get_random_manga(self, message: Message, state: FSMContext):
        response = await self.bot.api.get_random()
        if response.ok:
            await self.show_manga(message=message, manga=response.data, state=state)
            return

        await self.manga_server_error(
            message,
            error=(
                "По какой-то причине не удалось получить мангу\n"
                f"Код ошибки: {response.status}\n"
                f"Сообщение: {response.message}\n"
                "Попробуйте позже!"
            ),
        )

    async def _show_manga(self, message: Message, query: str, state: FSMContext):
        if manga := await self.get_manga(query):
            await self.show_manga(message=message, manga=manga, state=state)
            return

        await self.manga_not_found(message)
