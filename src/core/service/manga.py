import asyncio
import math

from typing import Protocol, Literal

from sqlalchemy import Select, select, func, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from ..entities.schemas import BaseManga, MangaFindResultSchema
from ..entities.models import Genre, GenreManga, Language, Author, Manga
from ..manager.manga import MangaManager


class HasManga(Protocol):
    @property
    def manga(self) -> Manga:
        """Манга"""


class FindService:
    BASE_PER_PAGE: int = 30

    def __init__(self, manager: MangaManager):
        self.manager = manager

    async def get_pages(
        self, page: int = 1, per_page: int | None = None
    ) -> MangaFindResultSchema:
        """
        Получает список манги для указанной страницы.

        Args:
            page (int): Номер страницы (начинается с 1).
            per_page (int | None): Количество манги на странице. По умолчанию — BASE_PER_PAGE.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.

        Returns:
            list[BaseManga]: Список манги без детальной информации.
        """
        per_page = per_page if per_page is not None else self.BASE_PER_PAGE
        print(per_page)
        self._number_biggest_zero(page)
        self._number_biggest_zero(per_page)

        base_query = select(Manga)
        query = (
            base_query.offset((page - 1) * (per_page))
            .limit(per_page)
            .order_by(desc(Manga.id))
        )

        manga, count = await asyncio.gather(
            self._scalars_manga(query),
            self._scalars_count(base_query),
        )

        return MangaFindResultSchema(
            query="ALL MANGA",
            succsess=True,
            total=count,
            response=manga,
            page=math.ceil((count or 0) / per_page),
            page_now=page,
        )

    async def get_pages_by_genre(
        self, genre_id: int, page: int = 1, per_page: int | None = None
    ) -> MangaFindResultSchema:
        """
        Получает список страниц манги по жанру.

        Args:
            genre_id (int): ID жанра.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        per_page = per_page if per_page is not None else self.BASE_PER_PAGE

        self._number_biggest_zero(page)
        self._number_biggest_zero(per_page)

        base_query = select(GenreManga).where(GenreManga.genre_id == genre_id)
        query = (
            base_query.options(selectinload(GenreManga.manga))
            .offset((page - 1) * (per_page))
            .limit(per_page)
            .order_by(desc(GenreManga.id))
        )

        manga, count = await asyncio.gather(
            self._scalars_manga(query),
            self._scalars_count(base_query),
        )

        return MangaFindResultSchema(
            query=f"FIND MANGA BY GENRE = {genre_id}",
            succsess=True,
            total=count,
            response=manga,
            page=math.ceil((count or 0) / per_page),
            page_now=page,
        )

    async def get_pages_by_author(
        self, author_id: int, page: int = 1, per_page: int | None = None
    ) -> MangaFindResultSchema:
        """
        Получает список страниц манги по автору.

        Args:
            author_id (int): ID автора.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        per_page = per_page or self.BASE_PER_PAGE

        self._number_biggest_zero(page)
        self._number_biggest_zero(per_page)

        base_query = select(Manga).where(Manga.author_id == author_id)
        query = (
            base_query.offset((page - 1) * (per_page))
            .limit(per_page)
            .order_by(desc(Manga.id))
        )

        manga, count = await asyncio.gather(
            self._scalars_manga(query),
            self._scalars_count(base_query),
        )

        return MangaFindResultSchema(
            query=f"FIND MANGA BY AUTHOR = {author_id}",
            succsess=True,
            total=count,
            response=manga,
            page=math.ceil((count or 0) / per_page),
            page_now=page,
        )

    async def get_pages_by_language(
        self, language_id: int, page: int = 1, per_page: int | None = None
    ) -> MangaFindResultSchema:
        """
        Получает список страниц манги по языку.

        Args:
            author_id (int): ID автора.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        per_page = per_page or self.BASE_PER_PAGE

        self._number_biggest_zero(page)
        self._number_biggest_zero(per_page)

        base_query = select(Manga).where(Manga.language_id == language_id)
        query = (
            base_query.offset((page - 1) * (per_page))
            .limit(per_page)
            .order_by(desc(Manga.id))
        )

        manga, count = await asyncio.gather(
            self._scalars_manga(query),
            self._scalars_count(base_query),
        )

        return MangaFindResultSchema(
            query=f"FIND MANGA BY LANGUAGE = {language_id}",
            succsess=True,
            total=count,
            response=manga,
            page=math.ceil((count or 0) / per_page),
            page_now=page,
        )

    async def get_pages_by_query(
        self, query: str, page: int = 1, per_page: int | None = None
    ) -> MangaFindResultSchema:
        """
        Получает список страниц манги по названию.

        Args:
            author_id (int): ID автора.

        Returns:
            list[BaseManga]: Список манги.

        Raises:
            ValueError: Если номер страницы меньше 1.
            ValueError: Если количество манги на странице меньше 1.
        """
        _find_query = query
        per_page = per_page or self.BASE_PER_PAGE
        if not query:
            raise ValueError("Запрос не может быть пустым")

        self._number_biggest_zero(page)
        self._number_biggest_zero(per_page)

        base_query = select(Manga).where(
            func.lower(Manga.title).contains(query.lower())
        )
        query = (
            base_query.offset((page - 1) * (per_page))
            .limit(per_page)
            .order_by(desc(Manga.id))
        )

        manga, count = await asyncio.gather(
            self._scalars_manga(query),
            self._scalars_count(base_query),
        )

        return MangaFindResultSchema(
            query=f"FIND MANGA BY QUERY = {_find_query}",
            succsess=True,
            total=count,
            response=manga,
            page=math.ceil((count or 0) / per_page),
            page_now=page,
        )

    async def get(
        self, id: int, param: Literal["genre", "author", "language"]
    ) -> str | None:
        """Получить название модели

        Args:
            id (int): ID модели
            param (Literal[&quot;genre&quot;, &quot;author&quot;, &quot;language&quot;]): Тип модели

        Raises:
            ValueError: Неверный параметр

        Returns:
            str | None: Название модели если найдено иначе None
        """
        model = None
        if "genre" == param:
            model = Genre
        elif "author" == param:
            model = Author
        elif "language" == param:
            model = Language
        else:
            raise ValueError(f"Неверный параметр: {param}")

        async with self.manager.Session() as session:
            result = await session.get(model, id)
            if result is None:
                logger.warning(f"Объект не найден (id={id}, param={param})")
                return None
            else:
                return result.name

    async def _get_by(
        self, selector: Select[tuple[Manga | HasManga]] | Manga
    ) -> MangaFindResultSchema:
        manga, count = await asyncio.gather(
            self._scalars_manga(selector),
            self._scalars_count(selector),
        )

        return MangaFindResultSchema(
            query=str(selector), succsess=True, total=count, response=manga
        )

    async def _scalars_manga(
        self, selector: Select[tuple[Manga | HasManga]]
    ) -> list[BaseManga]:
        """Делает запрос по Select и возращает мангу

        Args:
            selector (Select[tuple[Manga]]): Параметр для запроса

        Returns:
            list[BaseManga]: Результат поиска
        """
        async with self.Session() as session:
            if result := await session.scalars(selector):
                return [
                    self._build_manga(manga)
                    if isinstance(manga, Manga)
                    else self._build_manga(manga.manga)
                    for manga in result
                ]

            logger.info(f"Не удалось получить мангу по запросу (select={selector})")
            return []

    async def _scalars_count(self, selector: Select[tuple[Manga]]) -> int:
        """Делает запрос по Select и возращает количество найденной манги

        Args:
            selector (Select[tuple[Manga]]): Параметр для запроса

        Returns:
            int: Количество найденной манги
        """
        async with self.Session() as session:
            count = await session.scalar(
                select(func.count()).select_from(selector.subquery())
            )
            return count or 0

    def _build_manga(self, manga: Manga) -> BaseManga:
        """Создаёт схему BaseManga из Manga

        Args:
            manga (Manga): Манга из БД

        Returns:
            BaseManga: Базовая манга
        """
        return BaseManga(title=manga.title, poster=manga.poster, url=manga.url)

    def _number_biggest_zero(self, number: int) -> None:
        """Проверяет является ли число больше нуля

        Args:
            number (int): Число

        Raises:
            TypeError: Если указанный тип не наследник int
            ValueError: Если число меньше 1
        """
        if not isinstance(number, int):
            logger.error(f"Тип входных данных не является int (input={number})")
            raise TypeError(f"Тип входных данных не является int (input={number})")

        if number < 1:
            logger.error(f"Неверное число (number={number})")
            raise ValueError(f"Неверное число (number={number})")

    @property
    def Session(self):
        return self.manager.Session
