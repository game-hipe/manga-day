import asyncio

from typing import overload, Unpack
from pathlib import Path

import aiohttp
import aiofiles

from sqlalchemy.orm import joinedload
from sqlalchemy import select
from loguru import logger
from PIL import Image

from ..entities.models import Manga
from ..manager.request import RequestManager, RequestItem
from ..manager.manga import MangaManager


class DownloadManager: # TODO: ДОДЕЛАЙ МЕНЯ СУКА
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
                    joinedload(Manga.generated_pdf),
                    joinedload(Manga.gallery)
                )
                manga = await session.scalar(query)
                if manga is None:
                    logger.warning(f"Манга с артикулом {sku} не найдена")
                    return

                if manga.generated_pdf is not None:
                    return manga.generated_pdf
                
                tasks = [asyncio.create_task(self.session.get(url, 'read')) for url in manga.gallery.urls]
                
                async with aiofiles.tempfile.TemporaryDirectory() as tmp, aiofiles.tempfile.TemporaryDirectory() as png_tmp:
                    png_tmp_path = Path(png_tmp)
                    tmp_path = Path(tmp)
                    
                    for indx, task in enumerate(tasks):
                        response = await task
                        if response is not None:
                            write_path = tmp_path / f"{indx}.webp"
                            await self._write(write_path, response)
                            
                    [x for x in tmp_path.glob("*.webp")]
                        
                            
    async def _write(self, path: str, response: bytes):
        async with aiofiles.open(path, "wb") as file:
            await file.write(response)
            
    def convert(self, path: str | Path, new_path: str | Path):
        """Преобразует webp в png"""
        with Image.open(path).convert("RGB") as img:
            img.save(new_path)