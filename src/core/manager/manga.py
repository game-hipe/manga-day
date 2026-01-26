from typing import overload

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine
from loguru import logger

from ..entites.schemas import MangaSchema, OutputMangaSchema
from ..entites.models import Manga, Gallery, Language, Author, GenreManga, Genre


class MangaManager:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self.Session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)
    
    async def add_manga(self, manga: MangaSchema) -> OutputMangaSchema:
        async with self.Session() as session:
            async with session.begin():
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
                    title = title,
                    url = url,
                    poster = poster,
                    language_id = language.id if language is not None else None,
                    author_id = author.id if author  is not None else None
                )
                session.add(result)
                await session.flush()
                
                await self._connect(result, manga, session)
                
                return OutputMangaSchema(
                    title = manga.title,
                    poster = manga.poster,
                    url = manga.url,
                    genres = manga.genres,
                    author = manga.author,
                    language = manga.language,
                    gallery = manga.gallery,
                    id = result.id
                )
    
    async def get_manga(self, id: int) -> OutputMangaSchema | None:
        async with self.Session() as session:
            manga = await session.scalar(
                select(Manga)
                .where(Manga.id == id)
                .options(
                    joinedload(Manga.author),
                    joinedload(Manga.language),
                    selectinload(Manga.genres_connection).joinedload(GenreManga.genre),
                    joinedload(Manga.gallery)
                )
                .execution_options(populate_existing=True)
            )
            if manga is None:
                logger.warning(
                    f"Манга не найдене (id={id})"
                )
                return
            
            return self._build_manga(manga, id = manga.id)
                
    async def _connect(self, manga: Manga, manga_schema: MangaSchema, session: AsyncSession) -> None:
        for genre_name in manga_schema.genres:
            genre = await self._add_genre(session, genre_name)
            session.add(GenreManga(genre_id = genre.id, manga_id = manga.id))
    
        gallery = Gallery(
            urls = list(str(x) for x in manga_schema.gallery),
            manga_id = manga.id
        )
        session.add(gallery)
        
    async def _add_author(self, session: AsyncSession, author: str) -> Author:
        return await self._add_item(
            session,
            Author,
            author
        )

    async def _add_genre(self, session: AsyncSession, genre: str) -> Genre:
        return await self._add_item(
            session,
            Genre,
            genre
        )

    async def _add_language(self, session: AsyncSession, language: str) -> Language:
        return await self._add_item(
            session,
            Language,
            language
        )

    async def _add_item(
        self,
        session: AsyncSession,
        model: type[Author | Genre | Language],
        item: str
    ) -> Author | Genre | Language:
        if result := await session.scalar(select(model).where(model.name == item)):
            return result

        result = model(name = item)
        session.add(result)
        
        await session.flush()
        
        return result
    
    @overload
    def _build_manga(self, manga: Manga, id: int) -> OutputMangaSchema: ...
    
    @overload
    def _build_manga(self, manga: OutputMangaSchema, language_id: int, author_id: int) -> Manga: ...
    
    def _build_manga(
        self,
        manga: Manga | OutputMangaSchema,
        **kw
    ) -> OutputMangaSchema | Manga:
        if isinstance(manga, Manga):
            return OutputMangaSchema(
                title = manga.title,
                poster = manga.poster,
                url = manga.url,
                genres = manga.genres,
                author = manga.author.name,
                language = manga.language.name,
                gallery = manga.gallery.urls,
                **kw
            )
        elif isinstance(manga, OutputMangaSchema):
            return Manga(
                title = manga.title,
                url = str(manga.url),
                poster = str(manga.poster),
                **kw
            )