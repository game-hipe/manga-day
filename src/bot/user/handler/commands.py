from aiogram import F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from loguru import logger

from ._base import UserBaseHandler
from .._text import GREETING, HELP


class StartHandler(UserBaseHandler):
    def connect(self):
        self.message_register(self.start, Command("start"))
        self.message_register(self.help, Command("help"))
        self.message_register(self.message_download, Command("download"))
        self.callback_register(self.call_download, F.data.startswith("pdf"))

    async def start(self, message: Message, command: CommandObject):
        """Обработчик команды `/start`,
        если во время перехода на нашего бота будет аргумет, то мы считаем что это запрос на мангу

        Args:
            message (Message): Сообщение Telegram
            command (CommandObject): Команда Telegram
        """
        if command.args:
            manga = await self.get_manga(command.args)
            if manga is None:
                await message.answer(
                    self.build_error_message(
                        f"Не найдена манга по запросу {command.args}"
                    )
                )
                return

            await self.send_pdf(message=message, manga=manga)
            return

        await message.answer(GREETING)

    async def help(self, message: Message) -> None:
        """Обработчик команды `/help`

        Args:
            message (Message): Сообщение Telegram
        """
        await message.answer(HELP)

    async def message_download(self, message: Message) -> None:
        """Обработчик команды /download

        Args:
            message (Message): Сообщение Telegram
        """
        try:
            command, query = message.text.split(maxsplit=1)
        except ValueError:
            await message.answer(
                "Пожалуйста введите данные в виде <code>/download [АРТИКУЛ или URL]</code>"
            )
            return

        await self._send_pdf(message, query)

    async def call_download(self, call: CallbackQuery) -> None:
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

        await self._send_pdf(call.message, sku)

    async def _send_pdf(self, message: Message, query: str) -> None:
        """Отправка PDF

        Args:
            message (Message): Сообщение Telegram
            query (str): Артикул или URL
        """
        manga = await self.get_manga(query=query)
        if manga is None:
            await self.manga_not_found(message)
            return

        await self.send_pdf(message=message, manga=manga, delete_message=True)
