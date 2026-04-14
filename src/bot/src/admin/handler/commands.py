import asyncio
from typing import Any, Callable, TypeAlias, Awaitable

from aiogram import F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

from ...core.schemas import SpiderStatus
from ..._alert import StatusMessageHandler
from ._base import AdminBaseHandler
from .._text import GREETING, HELP

CommandCallback: TypeAlias = CallbackQuery | Message


class CommandsHandler(AdminBaseHandler):
    """Обработчик команд Telegram-бота для управления парсингом.

    Инициализирует маршрутизатор и регистрирует обработчики команд.
    Использует SpiderManager для управления жизненным циклом парсера.

    Args:
        spider_manager (SpiderManager): Экземпляр менеджера парсинга для управления запуском, остановкой и получением статуса.

    Attributes:
        router (Router): Маршрутизатор aiogram для регистрации обработчиков сообщений.
        spider_manager (SpiderManager): Ссылка на менеджер парсинга.
    """

    def __init__(self, bot, extra_kwargs=...):
        super().__init__(bot, extra_kwargs)
        self._last_handler: None | StatusMessageHandler = None

    def connect(self):
        """Регистрирует все обработчики команд в роутере.

        Обрабатывает следующие команды:
        - /start
        - /help
        - /start_parsing
        - /stop_parsing
        - /stop_spider
        - /start_spider
        - /status
        """
        self.message_register(self.start, Command("start"))
        self.message_register(self.help, Command("help"))
        self.message_register(self.start_parsing, Command("start_parsing"))
        self.message_register(self.stop_parsing, Command("stop_parsing"))
        self.message_register(self.stop_spider, Command("stop_spider"))
        self.message_register(self.start_spider, Command("start_spider"))
        self.message_register(self.update_spider, Command("update_status"))
        self.message_register(self.status, Command("status"))

        self.callback_register(self.start_spider_call, F.data.startswith("start:"))
        self.callback_register(self.stop_spider_call, F.data.startswith("stop:"))
        self.callback_register(self.update_spider_call, F.data.startswith("update:"))

    async def start(self, message: Message):
        """Отправляет приветственное сообщение при получении команды /start.

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        await message.answer(GREETING)

    async def help(self, message: Message):
        """Отправляет справочное сообщение при получении команды /help.

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        await message.answer(HELP)

    async def start_parsing(self, message: Message):
        """Запускает процесс парсинга по команде /start_parsing.

        Отправляет уведомление о попытке запуска,
        затем делегирует выполнение SpiderManager.

        Args:
            message (Message): Входящее сообщение от пользователя.

        Raises:
            Исключения могут быть выброшены методом start_parsing() SpiderManager.
        """
        await message.answer("Попытка начать парсинг")
        asyncio.create_task(self.api.spider("start", "all"))

    async def stop_parsing(self, message: Message):
        """Останавливает процесс парсинга по команде /stop_parsing.

        Отправляет уведомление о попытке остановки,
        затем делегирует выполнение SpiderManager.

        Args:
            message (Message): Входящее сообщение от пользователя.

        Raises:
            Исключения могут быть выброшены методом stop_parsing() SpiderManager.
        """
        await message.answer("Попытка остановить парсинг")
        asyncio.create_task(self.api.spider("stop", "all"))

    async def stop_spider(self, message: Message):
        """Останавливает спайдера по команде /stop_spider [spider_name].

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        try:
            _, spider_name = message.text.split()
            await self._stop_spider(spider_name, message)
        except ValueError:
            await message.answer(
                "Неверный формат команды. Используйте: /stop_spider [spider_name]"
            )

    async def start_spider(self, message: Message):
        """Запускает спайдер по команде /start_spider [spider_name].

        Args:
            message (Message): Входящее сообщение от пользователя.
        """
        try:
            _, spider_name = message.text.split()
            await self._start_spider(spider_name, message)
        except ValueError:
            await message.answer(
                "Неверный формат команды. Используйте: /start_spider [spider_name]"
            )

    async def update_spider(self, message: Message):
        try:
            _, spider_name = message.text.split()
            await self.api.spider("update", spider_name, message)
        except ValueError:
            await message.answer(
                "Неверный формат команды. Используйте: /update_spider [spider_name]"
            )

    async def status(self, message: Message):
        """Отправляет текущий статус парсера по команде /status.

        Args:
            message (Message): Входящее сообщение от пользователя.

        Raises:
            AttributeError: Если spider_manager не имеет атрибута status.
        """
        if self._last_handler:
            self._last_handler.deactivate()

        data = await self.api.status()
        keyboard = self._create_spider_keyboard(data)
        text = "\n".join(str(x) for x in data)

        result = await message.answer(
            text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        self._last_handler = StatusMessageHandler(result, self)
        self.bot.alert.add_handler(self._last_handler)

    async def start_spider_call(self, call: CallbackQuery):
        """Получает команду на старт парсера

        Args:
            call (CallbackQuery): Входящий запроса от пользователя.
        """
        await self._run_spider(
            call,
            self._start_spider,
            "Неверный формат команды. Используйте: /start_spider [spider_name]",
        )

    async def stop_spider_call(self, call: CallbackQuery):
        """Получает команду на остановку парсера

        Args:
            call (CallbackQuery): Входящий запроса от пользователя.
        """
        await self._run_spider(
            call,
            self._stop_spider,
            "Неверный формат команды. Используйте: /stop_spider [spider_name]",
        )

    async def update_spider_call(self, call: CallbackQuery):
        """Получает команду на обновление парсера"""
        try:
            _, spider_name = call.data.split(":", 1)
        except ValueError:
            await call.message.answer(
                "Неверный формат команды. Используйте: /update_spider [spider_name]"
            )
            return

        await self.api.spider("update", spider_name)

    async def _start_spider(self, spider_name: str, query: CommandCallback):
        """Начинает работу паука

        Args:
            spider_name (str): Название паука
            query (CommandCallback): Message или CallbackQuery
        """
        message = self._get_message(query)
        try:
            if spider_name == "all":
                await self.api.spider("start", "all")
                return
            if all(
                x.status == "running"
                for x in await self.api.status()
                if x.name == spider_name
            ):
                await message.answer(f"Спайдер {spider_name} уже запущен")
                return
            await self.api.spider("start", spider_name)
        except KeyError:
            await message.answer("Спайдер не найден.")

    async def _stop_spider(self, spider_name: str, query: CommandCallback):
        """Остонваливает работу паука

        Args:
            spider_name (str): Название паука
            query (CommandCallback): Message или CallbackQuery
        """
        message = self._get_message(query)
        try:
            if spider_name == "all":
                await self.api.spider("stop", "all")
                return
            if all(
                x.status == "not_running"
                for x in await self.api.status()
                if x.name == spider_name
            ):
                await message.answer(f"Спайдер {spider_name} уже остановлен")
                return
            await self.api.spider("stop", spider_name)
        except KeyError:
            await message.answer("Спайдер не найден.")

    def _create_spider_keyboard(
        self, data: list[SpiderStatus]
    ) -> list[list[InlineKeyboardButton]]:
        """Создать клавиатуру со статусами

        Returns:
            list[list[InlineKeyboardButton]]: Клавиатура со статусами
        """
        EMOJI_START = "▶️"
        EMOJI_UPDATE = "🔄"
        EMOJI_STOP = "⏹️"
        EMOJI_ALL = "🌐"
        EMOJI_RUNNING = "🟢"

        keyboard: list[list[InlineKeyboardButton]] = []

        for status in data:
            spider_name = status.name
            if status.status == "not_running":
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=f"{EMOJI_START} {spider_name}",
                            callback_data=f"start:{spider_name}",
                            style="success",
                        ),
                        InlineKeyboardButton(
                            text=f"{EMOJI_UPDATE} Обновить {spider_name}",
                            callback_data=f"update:{spider_name}",
                            style="success",
                        ),
                    ]
                )
            else:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=f"{EMOJI_STOP} Остановить {spider_name} {EMOJI_RUNNING}",
                            callback_data=f"stop:{spider_name}",
                            style="danger",
                        )
                    ]
                )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{EMOJI_ALL} Запустить все",
                    callback_data="start:all",
                    style="primary",
                )
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{EMOJI_STOP} Остановить все",
                    callback_data="stop:all",
                    style="danger",
                )
            ]
        )

        return keyboard

    @staticmethod
    def _get_message(query: CommandCallback) -> Message:
        if isinstance(query, CallbackQuery):
            if query.message is None:
                raise AttributeError("CallbackQuery.message Пуст")
            if isinstance(query.message, Message):
                return query.message
        return query

    async def _run_spider(
        self,
        call: CallbackQuery,
        func: Callable[[str, CallbackQuery], Awaitable[Any]],
        on_error: str,
    ):
        if call.data is None:
            await call.message.answer(on_error)  # type: ignore
            return

        try:
            _, spider_name = call.data.split(":", 1)
            await func(spider_name, call)

        except ValueError:
            await call.message.answer(on_error)  # type: ignore
