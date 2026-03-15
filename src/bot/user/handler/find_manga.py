from typing import TypedDict, Literal

from aiogram import Router, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ....core.entities.schemas import BaseManga
from ....core.manager import MangaManager
from ....core.service import FindService
from .._text import FIND_MANGA, ALL_FINDED_MANGA


class FindMangaStates(StatesGroup):
    browsing = State()
    """Указывает на то что человек находится в поиске"""


class FindArguments(TypedDict):
    page: int
    """Страница поиска начинается с 1"""

    query: str | int
    """Поиск, по запросу str если `query` в остальных случаях int"""

    name: Literal["author", "genre", "language", "query"] = "query"
    """Тип поиска ["author", "genre", "language", "query"]"""


class FindCommandsHandler:
    BASE_FIND_COUNT = 9
    """Количество манги за раз, число выбрано для красоты при пагинации"""

    MANGA_ON_KEYBOARD = 3
    """Количество манги на клавиатуре"""

    def __init__(self, manager: MangaManager, find: FindService):
        self.manager = manager
        self.find = find
        self.router = Router()
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.find_manga, Command("find"))
        self.router.message.register(self.browsing, FindMangaStates.browsing, F.text)
        self.router.callback_query.register(
            self.call_browsing, FindMangaStates.browsing, F.data.startswith("page")
        )

    async def find_manga(self, messsage: Message, state: FSMContext) -> None:
        await state.set_state(FindMangaStates.browsing)
        await state.set_data({"page": 1, "name": "query"})
        await messsage.answer("Введите запрос для поиска: ")

    async def browsing(self, message: Message, state: FSMContext) -> None:
        await state.set_data({"query": message.text})
        data: FindArguments = await state.get_data()
        count, mangas = await self.find.get_pages_by_query(
            data.get("query"), data.get("page", 1), self.BASE_FIND_COUNT
        )
        await self._show_manga(
            message,
            mangas=mangas,
            count=count,
            page=data.get("page", 1),
            query=data.get("query"),
            name=data.get("name"),
            state=state,
        )

    async def call_browsing(self, call: CallbackQuery, state: FSMContext) -> None:
        _, name, query, page = call.data.split(":")
        await state.set_data(
            {
                "name": name,
                "page": int(page),
                "query": int(query) if query.isdigit() else query,
            }
        )
        data: FindArguments = await state.get_data()
        count, mangas = await self.find.get_pages_by_query(
            data.get("query"), data.get("page", 1), self.BASE_FIND_COUNT
        )

        await self._show_manga(
            call.message,
            mangas=mangas,
            count=count,
            page=data.get("page", 1),
            query=data.get("query"),
            name=data.get("name"),
            state=state,
        )

    async def _show_manga(
        self,
        message: Message,
        mangas: list[BaseManga],
        count: int,
        page: int,
        query: str | int,
        name: str,
        state: FSMContext,
    ) -> None:
        """Показывает пользователю результат запроса

        Args:
            message (Message): Сообщение от пользователя
            mangas (list[BaseManga]): Манги
            count (int): Количество манг
            page (int): Текущая страница
            query (str | int): Запрос от пользователя
            name (str): Тип запроса Поддерживает следующие параметры ["author", "genre", "language", "query"]
        """
        media = self._create_media(mangas)
        text = self._create_text(mangas, count, query)
        keyboard = self._create_keyboard(mangas, count, page, query, name)
        if media:
            await message.answer_media_group(media=media)
        else:
            await state.clear()

        await message.answer(
            text=text, reply_markup=keyboard, disable_web_page_preview=True
        )

    def _create_keyboard(
        self,
        mangas: list[BaseManga],
        count: int,
        page: int,
        query: str | int,
        name: str,
    ) -> InlineKeyboardMarkup:
        """
        Создаёт inline-клавиатуру для отображения результатов поиска с пагинацией.

        Формирует клавиатуру с кнопками-ссылками на найденные манги (по self.MANGA_ON_KEYBOARD в ряд)
        и строкой навигации для переключения между страницами.

        Args:
            mangas (list[BaseManga]): Список объектов манги для текущей страницы.
                Каждый объект должен содержать title и url.
            count (int): Общее количество найденных результатов.
            page (int): Номер текущей страницы (начиная с 1).
            query (str | int): Поисковый запрос, используется в callback_data для пагинации.
            name (str): Тип/источник поиска, используется в callback_data для пагинации.

        Returns:
            InlineKeyboardMarkup: Клавиатура со следующей структурой:
                - Ряды кнопок с названиями манг (до self.MANGA_ON_KEYBOARD в ряду)
                Каждая кнопка ведёт на URL манги (внешняя ссылка)
                - Последний ряд с элементами пагинации:
                * "◀️ Назад" - если есть предыдущая страница (callback_data: "page:{name}:{query}:{page-1}")
                * Индикатор текущей страницы "X / Y" (callback_data: "current_page")
                * "▶️ Вперед" - если есть следующая страница (callback_data: "page:{name}:{query}:{page+1}")

        Example:
            Результат работы при self.MANGA_ON_KEYBOARD = 3:
            | Баки | Берсерк | Блич         |  ← каждая ведёт на свой URL
            | Наруто | Ванпанчмен | Токийский гуль |
            | ◀️ Назад | 2 / 5 | ▶️ Вперед   |  ← навигация

        Note:
            - Если после заполнения рядов остаются неиспользованные кнопки,
            они добавляются отдельным рядом
            - Ряд пагинации добавляется только если есть хотя бы одна кнопка навигации
            - Callback_data для кнопок пагинации формируется как f"page:{name}:{query}:{page}"
            - Кнопка с номером страницы имеет callback_data="current_page" и служит только для информации

        Raises:
            AttributeError: Если элементы mangas не имеют атрибутов title или url
        """
        keyboard = []
        items = []
        for indx, manga in enumerate(mangas, start=1):
            items.append(InlineKeyboardButton(text=manga.title, url=str(manga.url)))

            if indx % self.MANGA_ON_KEYBOARD == 0:
                keyboard.append(items)
                items = []

        keyboard.append(
            [
                button
                for button in [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data=f"page:{name}:{query}:{page - 1}"
                    )
                    if page > 1
                    else None,
                    InlineKeyboardButton(
                        text=f"{page} / {count}", callback_data="DONT_USEBLE"
                    ),
                    InlineKeyboardButton(
                        text="▶️ Вперед", callback_data=f"page:{name}:{query}:{page + 1}"
                    )
                    if count > page
                    else None,
                ]
                if button
            ]
        )
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    def _create_text(self, mangas: list[BaseManga], count: int, query: str) -> str:
        """Создание текста для отправки

        Args:
            mangas (list[BaseManga]): Базовая манга нужны лишь поля url, title, poster
            count (int): Количество найденой манги
            query (str): Запрос

        Returns:
            str: Текст
        """
        return ALL_FINDED_MANGA.format(
            count=count,
            query=query,
            mangas="\n".join(
                FIND_MANGA.format(title=manga.title, url=str(manga.url))
                for manga in mangas
            )
            or "Ничего не найдено по запросу!",
        )

    def _create_media(self, mangas: list[BaseManga]) -> list[InputMediaPhoto]:
        """Создаёт изображение для отправки

        Args:
            mangas (list[BaseManga]): Базовая манга нужны лишь поля url, title, poster

        Returns:
            list[InputMediaPhoto]: Список изображений для отправки
        """
        media = []
        for manga in mangas:
            media.append(InputMediaPhoto(media=str(manga.poster)))
        return media
