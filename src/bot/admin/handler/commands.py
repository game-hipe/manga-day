from typing import TypeAlias

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

from ....core.manager.spider import SpiderManager
from ....core.manager.spider._status import SpiderStatusEnum
from .._text import GREETING, HELP

CommandCallback: TypeAlias = CallbackQuery | Message


class CommandsHandler:
    """Обработчик команд Telegram-бота для управления парсингом.

    Инициализирует маршрутизатор и регистрирует обработчики команд.
    Использует SpiderManager для управления жизненным циклом парсера.

    Args:
        spider_manager (SpiderManager): Экземпляр менеджера парсинга для управления запуском, остановкой и получением статуса.

    Attributes:
        router (Router): Маршрутизатор aiogram для регистрации обработчиков сообщений.
        spider_manager (SpiderManager): Ссылка на менеджер парсинга.
    """

    def __init__(self, spider_manager: SpiderManager):
        """Инициализация обработчика команд.

        Создаёт экземпляр роутера и регистрирует обработчики команд.

        Args:
            spider_manager (SpiderManager): Менеджер для управления процессом парсинга.
        """
        self.router = Router()
        self.spider_manager = spider_manager
        self.register_handlers()

    def register_handlers(self):
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
        self.router.message.register(self.start, Command("start"))
        self.router.message.register(self.help, Command("help"))
        self.router.message.register(self.start_parsing, Command("start_parsing"))
        self.router.message.register(self.stop_parsing, Command("stop_parsing"))
        self.router.message.register(self.stop_spider, Command("stop_spider"))
        self.router.message.register(self.start_spider, Command("start_spider"))
        self.router.message.register(self.status, Command("status"))

        self.router.callback_query.register(
            self.start_spider_call, F.command.text.startswith("start:")
        )
        self.router.callback_query.register(
            self.stop_spider_call, F.command.text.startswith("stop:")
        )

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
        await self.spider_manager.start_full_parsing()

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
        await self.spider_manager.stop_all_spider()

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

    async def status(self, message: Message):
        """Отправляет текущий статус парсера по команде /status.

        Args:
            message (Message): Входящее сообщение от пользователя.

        Raises:
            AttributeError: Если spider_manager не имеет атрибута status.
        """
        keyboard = self._create_spider_keyboard()
        text = "\n".join(str(x) for x in self.spider_manager.status)

        await message.answer(
            text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

    async def start_spider_call(self, call: CallbackQuery):
        """Получает команду на старт парсера

        Args:
            call (CallbackQuery): Входящий запроса от пользователя.
        """
        try:
            _, spider_name = call.message.text.split(":", 1)
            await self._start_spider(spider_name, call)
        except ValueError:
            await call.message.answer(
                "Неверный формат команды. Используйте: /start_spider [spider_name]"
            )

    async def stop_spider_call(self, call: CallbackQuery):
        """Получает команду на остановку парсера

        Args:
            call (CallbackQuery): Входящий запроса от пользователя.
        """
        try:
            _, spider_name = call.message.text.split(":", 1)
            await self.spider_manager.starter.stop_spider(spider_name)
        except ValueError:
            await call.message.answer(
                "Неверный формат команды. Используйте: /stop_spider [spider_name]"
            )

    async def _start_spider(self, spider_name: str, query: CommandCallback):
        """Начинает работу паука

        Args:
            spider_name (str): Название паука
            query (CommandCallback): Message или CallbackQuery
        """
        message = self._get_message(query)
        try:
            if (
                self.spider_manager.get_spider_status(spider_name)
                == SpiderStatusEnum.RUNNING
            ):
                await message.answer(f"Спайдер {spider_name} уже запущен")
                return
            await self.spider_manager.starter.start_spider(spider_name)
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
            if (
                self.spider_manager.get_spider_status(spider_name)
                == SpiderStatusEnum.NOT_RUNNING
            ):
                await message.answer(f"Спайдер {spider_name} уже остановлен")
                return
            await self.spider_manager.starter.stop_spider(spider_name)
        except KeyError:
            await message.answer("Спайдер не найден.")

    def _create_spider_keyboard(self) -> list[list[InlineKeyboardButton]]:
        keyboard: list[list[InlineKeyboardButton]] = []
        for status in self.spider_manager.status:
            if status.status == SpiderStatusEnum.NOT_RUNNING:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text="Запуск", callback_data=f"start:{status.name}"
                        )
                    ]
                )
            else:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text="Остановка", callback_data=f"stop:{status.name}"
                        )
                    ]
                )

        return keyboard

    @staticmethod
    def _get_message(query: CommandCallback) -> Message:
        if isinstance(query, CallbackQuery):
            return query.message
        return query
