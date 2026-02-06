from typing import overload, Unpack

import aiohttp
import aiofiles

from sqlalchemy.orm import joinedload
from sqlalchemy import select
from loguru import logger

from ..entities.models import Manga, GeneratedPdf
from .request import RequestManager, RequestItem
from .manga import MangaManager


class DownloadManager:
    """Класс для скачивания манги"""

    BASE_PATH: str = "."
    
    @overload
    def __init__(self, session: RequestManager, manager: MangaManager) -> None: ...
    
    @overload
    def __init__(self, session: aiohttp.ClientSession, manager: MangaManager, **kwargs: Unpack[RequestItem]) -> None: ...
    
    def __init__(self, session: RequestManager | aiohttp.ClientSession, manager: MangaManager, **kwargs) -> None:
        if isinstance(session, RequestManager):
            self.session = session
        else:
            self.session = RequestManager(session, **kwargs)

        self.manager = manager
        
    async def download(self, sku: str, path: str | None = None):
        """Метод для скачивания PDF"""
        async with self.manager.Session() as session:
            async with session.begin():
                query = select(Manga).where(Manga.sku == sku).options(
                    joinedload(Manga.generated_pdf)
                )
                manga = await session.scalar(query)
                if manga is None:
                    logger.warning(f"Манга с артикулом {sku} не найдена")
                    return

                if manga.generated_pdf is not None:
                    return manga.generated_pdf
                
                