from typing import overload

from sqlalchemy import func, delete

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine
from loguru import logger

from ..entities.schemas import (
    MangaSchema,
    OutputMangaSchema,
    BaseManga,
    ObjectWithId,
)
from ..entities.models import Manga, Gallery, Language, Author, GenreManga, Genre
from .._tools import logging


class MangaManager:
    """
    Менеджер для асинхронной работы с данными манги в базе данных.

    Предоставляет методы для добавления, получения и фильтрации манги,
    а также взаимодействия с авторами, жанрами, языками и галереями.
    Использует SQLAlchemy для асинхронного доступа к базе данных.

    Атрибуты:
        BASE_PER_PAGE (int): Количество манги на одной странице по умолчанию.
    """

    BASE_PER_PAGE: int = 30

    def __init__(self, engine: AsyncEngine):
        """
        Инициализирует менеджер манги.

        Args:
            engine (AsyncEngine): Асинхронный движок SQLAlchemy для подключения к БД.
        """
        self._engine = engine
        self.Session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)

    @logging
    async def add_manga(self, manga: MangaSchema) -> OutputMangaSchema:
        """
        Добавляет новую мангу в базу данных.

        При необходимости создаёт или получает существующие записи:
        язык, автор, жанры, галерея. Связывает их с мангой.

        Args:
            manga (MangaSchema): Схема данных новой манги.

        Returns:
            OutputMangaSchema: Добавленная манга с заполненными ID и связями. OutputMangaSchema, если манга уже существует.
        """
        async with self.Session() as session:
            async with session.begin():
                find_manga = await session.scalar(
                    select(Manga)
                    .where(Manga.sku == manga.sku)
                    .options(
                        joinedload(Manga.author),
                        joinedload(Manga.language),
                        selectinload(Manga.genres_connection).joinedload(
                            GenreManga.genre
                        ),
                        joinedload(Manga.gallery),
                    )
                    .execution_options(populate_existing=True)
                )
                if find_manga is not None:
                    logger.warning(f"Манга уже существует (sku={find_manga.sku})")
                    return self._build_manga(find_manga, id=find_manga.id)

                title = manga.title
                url = str(manga.url)
                poster = str(manga.poster)

                language = None
                author = None

                if manga.language:
                    language = await self._add_language(session, manga.language)

                if manga.author:
                    author = await self._add_author(session, manga.author)

                result = Manga(
                    title=title,
                    url=url,
                    poster=poster,
                    language_id=language.id if language is not None else None,
                    author_id=author.id if author is not None else None,
                )
                session.add(result)
                await session.flush()

                genres = await self._connect(result, manga, session)

                return OutputMangaSchema(
                    title=manga.title,
                    poster=manga.poster,
                    url=manga.url,
                    genres=genres,
                    author=ObjectWithId(name=manga.author, id=author.id)
                    if author
                    else None,
                    language=ObjectWithId(name=manga.language, id=language.id)
                    if language
                    else None,
                    gallery=manga.gallery,
                    id=result.id,
                )

    @logging
    async def update_manga(
        self,
        sku: str,
        *,
        title: str | None = None,
        url: str | None = None,
        poster: str | None = None,
        language: str | None = None,
        author: str | None = None,
        gallery: list[str] | None = None,
        genres: list[str] | None = None,
    ) -> OutputMangaSchema | None:
        """Обновить мангу
        Если не указан параметр, то он не будет обновлен

        Args:
            sku (str): _description_
            title (str | None, optional): Название. По умолчанию None.
            url (str | None, optional): URL. По умолчанию None.
            poster (str | None, optional): Постер. По умолчанию None.
            language (str | None, optional): Язык. По умолчанию None.
            author (str | None, optional): Автор. По умолчанию None.
            gallery (list[str] | None, optional): Галлерея. По умолчанию None.
            genres (list[str] | None, optional): Жанры. По умолчанию None.

        Returns:
            OutputMangaSchema | None: Схема данных манги. Если манга не найдена, то None.
        """
        async with self.Session() as session:
            async with session.begin():
                find_manga = await session.scalar(
                    select(Manga)
                    .where(Manga.sku == sku)
                    .options(
                        joinedload(Manga.author),
                        joinedload(Manga.language),
                        selectinload(Manga.genres_connection).joinedload(
                            GenreManga.genre
                        ),
                        joinedload(Manga.gallery),
                    )
                    .execution_options(populate_existing=True)
                )
                if find_manga is None:
                    logger.warning(f"Манга не существует (sku={sku})")
                    return None

                if title is not None:
                    find_manga.title = title

                if url is not None and find_manga.url != str(url):
                    find_manga.url = str(url)

                if poster is not None and find_manga.poster != str(poster):
                    find_manga.poster = str(poster)

                if language is not None and find_manga.language != language:
                    find_manga.language_id = (
                        await self._add_language(session, language)
                    ).id

                if author is not None and find_manga.author != author:
                    find_manga.author_id = (await self._add_author(session, author)).id

                if genres is not None:
                    await session.execute(
                        delete(GenreManga).where(GenreManga.manga_id == find_manga.id)
                    )
                    for genre in genres:
                        genre = await self._add_genre(session, genre)
                        session.add(
                            GenreManga(manga_id=find_manga.id, genre_id=genre.id)
                        )

                if gallery is not None:
                    await session.execute(
                        delete(Gallery).where(Gallery.manga_id == find_manga.id)
                    )
                    gallery = Gallery(
                        urls=[str(x) for x in gallery], manga_id=find_manga.id
                    )
                    session.add(gallery)

                await session.flush()
                return self._build_manga(find_manga, id=find_manga.id)

    @logging
    async def get_manga(self, id: int) -> OutputMangaSchema | None:
        """
        Получает мангу по её идентификатору.

        Загружает все связанные данные: автора, язык, жанры, галерею.

        Args:
            id (int): Уникальный идентификатор манги.

        Returns:
            OutputMangaSchema | None: Данные манги или None, если не найдена.
        """
        async with self.Session() as session:
            manga = await session.scalar(
                select(Manga)
                .where(Manga.id == id)
                .options(
                    joinedload(Manga.author),
                    joinedload(Manga.language),
                    selectinload(Manga.genres_connection).joinedload(GenreManga.genre),
                    joinedload(Manga.gallery),
                )
                .execution_options(populate_existing=True)
            )
            if manga is None:
                logger.debug(f"Манга не найдена (id={id})")
                return None

            return self._build_manga(manga, id=manga.id)

    @logging
    async def get_manga_by_url(self, url: str) -> OutputMangaSchema | None:
        """
        Получает мангу по её URL.

        Загружает все связанные данные: автора, язык, жанры, галерею.

        Args:
            url (str): URL манги.

        Returns:
            OutputMangaSchema | None: Данные манги или None, если не найдена.
        """
        async with self.Session() as session:
            manga = await session.scalar(
                select(Manga)
                .where(Manga.url == url)
                .options(
                    joinedload(Manga.author),
                    joinedload(Manga.language),
                    selectinload(Manga.genres_connection).joinedload(GenreManga.genre),
                    joinedload(Manga.gallery),
                )
                .execution_options(populate_existing=True)
            )
            if manga is None:
                logger.debug(f"Манга не найдена (url={url})")
                return None

            return self._build_manga(manga, id=manga.id)

    @logging
    async def get_manga_by_sku(self, sku: str) -> OutputMangaSchema | None:
        """
        Получает мангу по её SKU.

        Загружает все связанные данные: автора, язык, жанры, галерею.

        Args:
            sku (str): sku манги.

        Returns:
            OutputMangaSchema | None: Данные манги или None, если не найдена.
        """
        async with self.Session() as session:
            manga = await session.scalar(
                select(Manga)
                .where(Manga.sku == sku)
                .options(
                    joinedload(Manga.author),
                    joinedload(Manga.language),
                    selectinload(Manga.genres_connection).joinedload(GenreManga.genre),
                    joinedload(Manga.gallery),
                )
                .execution_options(populate_existing=True)
            )
            if manga is None:
                logger.debug(f"Манга не найдена (sku={sku})")
                return None

            return self._build_manga(manga, id=manga.id)

    @logging
    async def in_database(self, manga: BaseManga) -> bool:
        """Проверяет наличие манги в базе данных

        Args:
            manga (BaseManga): непосредственно сама манга

        Returns:
            bool: True если манга уже есть в базе данных, иначе False
        """
        async with self.Session() as session:
            db_manga = None
            try:
                db_manga = await session.scalar(
                    select(Manga).where(Manga.sku == manga.sku)
                )
                if db_manga:
                    return True

                return False
            finally:
                if db_manga is not None and db_manga.poster != str(manga.poster):
                    db_manga.poster = str(manga.poster)
                    await session.commit()

    @logging
    async def get_total(self) -> int:
        """Получить общее количество манги в базе данных"""
        async with self.Session() as session:
            total = await session.scalar(select(func.count()).select_from(Manga))
            return total or 0

    async def _connect(
        self, manga: Manga, manga_schema: MangaSchema, session: AsyncSession
    ) -> list[ObjectWithId]:
        """
        Связывает мангу с жанрами и галереей.

        Создаёт записи в таблицах связи и добавляет галерею.

        Args:
            manga (Manga): Объект манги из БД.
            manga_schema (MangaSchema): Входные данные манги.
            session (AsyncSession): Активная сессия БД.

        Returns:
            list[ObjectWithId]: Список связанных объектов.

        """
        result: list[ObjectWithId] = []
        for genre_name in manga_schema.genres:
            genre = await self._add_genre(session, genre_name)
            session.add(GenreManga(genre_id=genre.id, manga_id=manga.id))
            result.append(ObjectWithId(id=genre.id, name=genre.name))

        gallery = Gallery(
            urls=[str(x) for x in manga_schema.gallery], manga_id=manga.id
        )
        session.add(gallery)
        return result

    async def _add_author(self, session: AsyncSession, author: str) -> Author:
        """
        Добавляет автора в БД или возвращает существующего.

        Args:
            session (AsyncSession): Активная сессия БД.
            author (str): Имя автора.

        Returns:
            Author: Объект автора.
        """
        return await self._add_item(session, Author, author)

    async def _add_genre(self, session: AsyncSession, genre: str) -> Genre:
        """
        Добавляет жанр в БД или возвращает существующий.

        Args:
            session (AsyncSession): Активная сессия БД.
            genre (str): Название жанра.

        Returns:
            Genre: Объект жанра.
        """
        return await self._add_item(session, Genre, genre)

    async def _add_language(self, session: AsyncSession, language: str) -> Language:
        """
        Добавляет язык в БД или возвращает существующий.

        Args:
            session (AsyncSession): Активная сессия БД.
            language (str): Название языка.

        Returns:
            Language: Объект языка.
        """
        return await self._add_item(session, Language, language)

    async def _add_item(
        self, session: AsyncSession, model: type[Author | Genre | Language], item: str
    ) -> Author | Genre | Language:
        """
        Универсальный метод для добавления сущности (автор, жанр, язык).

        Проверяет наличие записи по имени, при отсутствии создаёт новую.

        Args:
            session (AsyncSession): Активная сессия БД.
            model (type[Author | Genre | Language]): Модель сущности.
            item (str): Имя сущности.

        Returns:
            Author | Genre | Language: Найденная или созданная сущность.
        """
        if result := await session.scalar(select(model).where(model.name == item)):
            return result

        result = model(name=item)
        session.add(result)
        await session.flush()
        return result

    @overload
    def _build_manga(self, manga: Manga, id: int) -> OutputMangaSchema: ...

    @overload
    def _build_manga(
        self, manga: OutputMangaSchema, language_id: int, author_id: int
    ) -> Manga: ...

    def _build_manga(
        self, manga: Manga | OutputMangaSchema, **kw
    ) -> OutputMangaSchema | Manga:
        """
        Преобразует объект между моделью БД и выходной схемой.

        Перегруженная функция:
         - Из Manga -> OutputMangaSchema
         - Из OutputMangaSchema -> Manga

        Args:
            manga (Manga | OutputMangaSchema): Входной объект.
            **kw: Дополнительные поля (например, id, language_id, author_id).

        Returns:
            OutputMangaSchema | Manga: Преобразованный объект.
        """
        if isinstance(manga, Manga):
            return OutputMangaSchema(
                title=manga.title,
                poster=manga.poster,
                url=manga.url,
                genres=[
                    ObjectWithId(name=genre.name, id=genre.id) for genre in manga.genres
                ],
                author=ObjectWithId(name=manga.author.name, id=manga.author_id)
                if manga.author
                else None,
                language=ObjectWithId(name=manga.language.name, id=manga.language_id)
                if manga.language
                else None,
                gallery=manga.gallery.urls,
                **kw,
            )
        elif isinstance(manga, OutputMangaSchema):
            return Manga(
                title=manga.title, url=str(manga.url), poster=str(manga.poster), **kw
            )
