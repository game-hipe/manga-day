"""Базовый хэндлер"""

from pathlib import Path
from random import choice
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any
from enum import Enum
from functools import wraps

from aiogram import Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import FSInputFile, Message
from loguru import logger

_T = TypeVar("_T")


class Smiles(Enum):
    DISAPPOINTED_SMILES = [
        "(ﾉД`)",  # Классический разочарованный/плачущий
        "(；一_一)",  # Разочарованный/смущенный
        "(￣～￣)",  # Недовольный/разочарованный
        "(￢_￢)",  # Смотрящий с подозрением/разочарованием
        "(-_-)",  # Равнодушный/разочарованный
        "(╯︵╰,)",  # Грустный/разочарованный
        "(｡•́︿•̀｡)",  # Грустное лицо
        "(´-﹏-`；)",  # Расстроенный
        "(⇀‸↼‶)",  # Недовольный
        "(；￣Д￣)",  # Разочарованный/шокированный
        "(；一ω一)",  # Унылый
        "(；′⌒`)",  # Плачущий от разочарования
        "(ᗒᗩᗕ)",  # Разочарованный/расстроенный
        "(◞‸◟)",  # Грустный/разочарованный
        "(´-`).｡oO()",  # Задумчивый/разочарованный
        "(；へ：)",  # Сильно расстроенный
        "(；^ω^）",  # Нервная улыбка от разочарования
        "(；一｀д´)",  # Раздраженный/разочарованный
        "【´д｀】",  # Уставший/разочарованный
        "(；´Д｀)",  # В шоке/разочаровании
    ]

    HAPPY_SMILES = [
        "(＾▽＾)",  # Радостный/счастливый
        "(◕‿◕)",  # Милый радостный
        "(✧ω✧)",  # Сияющий от счастья
        "ヽ(♡‿♡)ノ",  # Очень счастливый с сердечками
        "(｡♥‿♥｡)",  # Влюбленный/счастливый
        "(≧◡≦)",  # Сияющая улыбка
        "(★‿★)",  # Счастливый со звездочками в глазах
        "ヾ(≧▽≦)ノ",  # Прыгающий от радости
        "(●＾o＾●)",  # Милый счастливый
        "ᕙ(▀̿̿Ĺ̯̿̿▀̿ ̿)ᕗ",  # Крутой/довольный
        "(◕‿◕✿)",  # Счастливый с цветочком
        "٩(◕‿◕｡)۶",  # Танцующий от радости
        "〜(꒪꒳꒪)〜",  # Мечтательный/счастливый
        "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",  # Счастливый с блестками
        "\\(★ω★)/",  # Радостный с поднятыми руками
        "✧⁺⸜(●′▾‵●)⸝⁺✧",  # Очень счастливый
        "(´ ∀ ` *)",  # Мило улыбающийся
        "♡(◕ᗜ◕)♡",  # Счастливый с сердечками
        "(｀∀´)Ψ",  # Хитро-довольный
        "٩(｡•́‿•̀｡)۶",  # Радостно машущий
        "(*＾▽＾)／",  # Приветливо-радостный
        "ヽ(｡◕o◕｡)ﾉ",  # Ликующий
        "(｡’▽’｡)♡",  # Счастливый влюбленный
        "★⌒ヽ(●’､’●)ﾉ",  # Радостный со звездочкой
        "ヽ(・∀・)ﾉ",  # Простой радостный
    ]


class BaseHandler(ABC, Generic[_T]):
    """Базовый хэндлер"""

    PATH_TO_404 = Path("src/frontend/user/static/images/404.png")
    PATH_TO_500 = Path("src/frontend/user/static/images/500.jpg")

    def __init__(self, bot: _T, extra_kwargs: dict[str, Any] = {}) -> None:
        """Хэндлер для aiogram бота

        Args:
            bot (_T): Бот от которого работает хэндлер
            extra_kwargs (dict[str, Any]): Дополнительные аргументы
        """
        self._bot = bot
        self._router = Router()
        self.extra_kwargs = extra_kwargs

        self.message_register = self._router.message.register
        self.callback_register = self._router.callback_query.register

        self._not_found_id: None | str = None
        self._error_id: None | str = None

        self.connect()

    @abstractmethod
    def connect(self) -> None:
        """Подключить handler-ы для бота"""

    def build_error_message(self, message: str) -> str:
        """Создаёт грустные сообщение

        Args:
            message (str): Сообщение которое будет использовано

        Returns:
            str: Получившееся сообщение

        Example:

            >>> build_error_message("Hello")
            >>> Hello (；一ω一)
        """
        return f"{message} {choice(Smiles.DISAPPOINTED_SMILES.value)}"

    def build_success_message(self, message: str) -> str:
        """Создаёт счастливые сообщение

        Args:
            message (str): Сообщение которое будет использовано

        Returns:
            str: Получившееся сообщение

        Example:

            >>> build_success_message("Hello")
            >>> Hello (＾▽＾)
        """
        return f"{message} {choice(Smiles.HAPPY_SMILES.value)}"

    async def manga_not_found(
        self, message: Message, error: str = "Манга не найдено"
    ) -> Message:
        """Присылает сообщение по типу "Манга не найдено"

        Args:
            message (Message): Сообщение от пользователя

        Returns:
            Message: Сообщение от бота о том что манга не найдена
            error (str): Текст ошибки
        """
        text = self.build_error_message(error)
        try:
            message_with_image = await message.answer_photo(
                photo=self.image_not_found,
                caption=text,
            )
            self.image_not_found = message_with_image
        except TelegramBadRequest:
            await message.answer(text)

    async def manga_server_error(
        self, message: Message, error: str = "Что-то пошло не так"
    ) -> Message:
        """Присылает сообщение по типу "Ошибка сервера"

        Args:
            message (Message): Сообщение от пользователя

        Returns:
            Message: Сообщение от бота о том что что-то пошло не так
            error (str): Текст ошибки
        """
        text = self.build_error_message(error)
        try:
            message_with_image = await message.answer_photo(
                photo=self.image_server_error,
                caption=text,
            )
            self.image_server_error = message_with_image
        except TelegramBadRequest:
            await message.answer(text)

    @property
    def bot(self) -> _T:
        """
        Бот от которого работает Handler
        """
        return self._bot

    @property
    def router(self) -> Router:
        """
        Роутер
        """
        return self._router

    @property
    def image_not_found(self) -> str | FSInputFile:
        """Возвращает изображение ID если сообщение было отправлено ранее иначе FSInputFile"""
        if self._not_found_id:
            return self._not_found_id
        return FSInputFile(self.PATH_TO_404)

    @image_not_found.setter
    def image_not_found(self, value: Message):
        if not isinstance(value, Message):
            raise TypeError(
                f"Неверный тип данных, ожидается Message, а получен {type(value).__name__}"
            )

        if not value.photo:
            raise ValueError("Сообщение должно содержать фото")

        self._not_found_id = value.photo[0].file_id

    @property
    def image_server_error(self) -> str | FSInputFile:
        """Возвращает изображение ID если сообщение было отправлено ранее иначе FSInputFile"""
        if self._error_id:
            return self._error_id
        return FSInputFile(self.PATH_TO_500)

    @image_server_error.setter
    def image_server_error(self, value: Message):
        if not isinstance(value, Message):
            raise TypeError(
                f"Неверный тип данных, ожидается Message, а получен {type(value).__name__}"
            )

        if not value.photo:
            raise ValueError("Сообщение должно содержать фото")

        self._error_id = value.photo[0].file_id


def send_on_error(on_error: str):
    """
    Декоратор: при ошибке в обработчике отправляет пользователю фото с сообщением об ошибке.

    Args:
        on_error (str): Текст ошибки, который будет показан пользователю.
    """

    def wrapper(func):
        logger.debug(f"Обработчик {func.__name__} будет обрабатывать ошибки")

        @wraps(func)
        async def inner(self: "BaseHandler", message: Message, *args, **kwargs):
            try:
                return await func(self, message, *args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в функции {func.__name__}: {e}", exc_info=True)
                try:
                    if message.from_user:
                        await self.manga_server_error(message, on_error)

                except TelegramAPIError as te:
                    logger.warning(
                        f"Не удалось отправить сообщение об ошибке пользователю: {te}"
                    )
                except Exception as ue:
                    logger.warning(
                        f"Неожиданная ошибка при отправке ошибки пользователю: {ue}"
                    )

            finally:
                text = getattr(message, "text", None) or getattr(
                    message, "caption", None
                )
                safe_text = (text[:50] + "...") if text and len(text) > 50 else text
                logger.debug(f"Вызов функции {func.__name__}, текст: {safe_text}")

        return inner

    return wrapper
