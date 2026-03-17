"""Базовый хэндлер"""

from random import choice
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any
from enum import Enum

from aiogram import Router

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
        "\(★ω★)/",  # Радостный с поднятыми руками
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
