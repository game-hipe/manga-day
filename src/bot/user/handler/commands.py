from aiogram import F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from ._base import UserBaseHandler
from .._text import GREETING, HELP


class DownloadStates(StatesGroup):
    download = State()


class StartHandler(UserBaseHandler):
    def connect(self):
        self.message_register(self.start, Command("start"))
        self.message_register(self.help, Command("help"))
        self.message_register(self.message_download, Command("download"))
        self.message_register(self.download_user, DownloadStates.download)
        self.callback_register(self.call_download, F.data.startswith("pdf"))

    async def start(self, message: Message, command: CommandObject, state: FSMContext):
        """Обработчик команды `/start`,
        если во время перехода на нашего бота будет аргумет, то мы считаем что это запрос на мангу

        Args:
            message (Message): Сообщение Telegram
            command (CommandObject): Команда Telegram
        """
        if command.args:
            await self._send_pdf(message, command.args, state)
            return

        await message.answer(GREETING)

    async def help(self, message: Message) -> None:
        """Обработчик команды `/help`

        Args:
            message (Message): Сообщение Telegram
        """
        await message.answer(HELP)

    async def message_download(self, message: Message, state: FSMContext) -> None:
        """Обработчик команды /download

        Args:
            message (Message): Сообщение Telegram
        """
        try:
            command, query = message.text.split(maxsplit=1)
        except ValueError:
            await state.set_state(DownloadStates.download)
            await message.answer("Введите URL либо артикул:")
            return

        await self._send_pdf(message, query, state)

    async def download_user(self, message: Message, state: FSMContext) -> None:
        """Обработчик команды /download"""
        try:
            await self._send_pdf(message, message.text, state)
        finally:
            await state.set_state(state=None)

    async def call_download(self, call: CallbackQuery, state: FSMContext) -> None:
        """Обработчик команды если CallbackQuery.data имеет начало `pdf:`

        Args:
            call (CallbackQuery): CallbackQuery Telegram
        """
        try:
            command, sku = call.data.split(":", maxsplit=1)
        except ValueError:
            logger.error(f"Не удалось получить sku (data={call.data})")
            await call.message.answer(
                self.build_error_message("Не удалось получить SKU манги")
            )

        await self._send_pdf(call.message, sku, state)

    async def _send_pdf(self, message: Message, query: str, state: FSMContext) -> None:
        """Отправка PDF

        Args:
            message (Message): Сообщение Telegram
            query (str): Артикул или URL
        """

        if await state.get_value("download-pdf"):
            await message.answer(
                self.build_error_message(
                    "Пожалуйста дождитесь окончания загрузки предыдущей манги"
                )
            )
            return

        manga = await self.get_manga(query=query)
        if manga is None:
            await self.manga_not_found(message)
            return

        try:
            await state.update_data({"download-pdf": True})
            await self.send_pdf(message=message, manga=manga, delete_message=True)

        finally:
            await state.update_data({"download-pdf": False})
