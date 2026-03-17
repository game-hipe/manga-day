from typing import TypedDict, Literal

from aiogram import F
from aiogram.filters import Command
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from ....core.entities.schemas import BaseManga
from .._text import FIND_MANGA, ALL_FINDED_MANGA

from ._base import UserBaseHandler


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


class FindCommandsHandler(UserBaseHandler):
    BASE_FIND_COUNT = 9
    """Количество манги за раз, число выбрано для красоты при пагинации"""

    MANGA_ON_KEYBOARD = 3
    """Количество манги на клавиатуре"""

    def connect(self):
        self.message_register(self.find_manga, Command("find"))
        self.message_register(self.browsing, FindMangaStates.browsing, F.text)
        self.callback_register(
            self.call_browsing, FindMangaStates.browsing, F.data.startswith("page:")
        )

    async def find_manga(self, messsage: Message, state: FSMContext) -> None:
        """Ищет мангу отвечает за команду `/find`

        Args:
            messsage (Message): Сообщение Telegram
            state (FSMContext): Контекст FSM
        """
        await state.set_state(FindMangaStates.browsing)
        await state.set_data({"page": 1, "name": "query"})

        await messsage.answer("Введите запрос для поиска: ")

    async def browsing(self, message: Message, state: FSMContext) -> None:
        """Указывает на то-что человек находится в поисковом состоянии

        Args:
            message (Message): Сообщение Telegram
            state (FSMContext): Контекст FSM
        """
        await state.update_data({"query": message.text})

        await self._show_manga(await state.get_data(), message, state)

    async def call_browsing(self, call: CallbackQuery, state: FSMContext) -> None:
        """Обрабоатывает нажатие на кнопку если в начале стоит `page:`

        Args:
            call (CallbackQuery): Что выдало нажатие на кнопку
            state (FSMContext): Контекст FSM
        """
        try:
            command, name, query, page = call.data.split(":")
        except ValueError:
            logger.error(f"Не удалось получить данные (data={call.data})")
            await call.message.answer("Не удалось получить данные")
            return

        await state.set_data(
            {
                "name": name,
                "page": int(page),
                "query": int(query) if name != "query" else query,
            }
        )

        await self._show_manga(await state.get_data(), call.message, state)

    async def _show_manga(
        self, data: FindArguments, message: Message, state: FSMContext
    ) -> None:
        """Показывает мангу из результатов FindArguments

        Args:
            data (FindArguments): Аргументы поиска
            message (Message): Сообщение Telegram
            state (FSMContext): Контекст FSM
        """
        count, mangas = await self.bot.find_service.get_pages_by_query(
            query=data["query"], page=data.get("page", 1), per_page=self.BASE_FIND_COUNT
        )

        media = self._build_find_media(mangas)
        keyboard = self._build_find_keyboard(data, mangas, count)
        text = self._build_find_text(data, mangas, count)

        if media:
            try:
                await message.answer_media_group(media=media)
            except TelegramBadRequest:
                await message.answer_photo(
                    FSInputFile(path=str("src/frontend/user/static/images/500.jpg")),
                    caption=text,
                    reply_markup=keyboard,
                )
                return
        else:
            await state.clear()

        await message.answer(
            text=text, reply_markup=keyboard, disable_web_page_preview=True
        )

    def _build_find_text(
        self, data: FindArguments, mangas: list[BaseManga], count: int
    ) -> str:
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
            query=data["query"],
            mangas="\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n".join(
                FIND_MANGA.format(
                    title=manga.title[:40] + "..."
                    if manga.title[:40] != manga.title
                    else "",
                    url=str(manga.url),
                )
                for manga in mangas
            )
            or "Ничего не найдено по запросу!",
        )

    def _build_find_keyboard(
        self, data: FindArguments, mangas: list[BaseManga], count: int
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

        name = data["name"]
        query = data["query"]
        page = data["page"]

        for indx, manga in enumerate(mangas, start=1):
            items.append(
                InlineKeyboardButton(
                    text=manga.title, callback_data=f"show:{manga.sku}"
                )
            )

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

    def _build_find_media(self, mangas: list[BaseManga]) -> list[InputMediaPhoto]:
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
