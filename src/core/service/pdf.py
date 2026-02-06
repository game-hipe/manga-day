import asyncio

from concurrent.futures import ThreadPoolExecutor
from typing import overload, Unpack
from pathlib import Path

import aiohttp
import aiofiles

from loguru import logger
from PIL import Image
from PIL.Image import Image as IMG

from ..entities.schemas import MangaSchema
from ..manager.request import RequestManager, RequestItem


class PDFService:
    """
    Класс для преоброзование фоток в PDF

    Основной метод:
        download(gallery, path) - Скачивает фотки, и сохраняет в виде PDF

    NOTE:
        В будущем можно добавить REDIS, для кэширование
    """

    BASE_PATH: str = "."
    BASE_MAX_WORKER: int = 5
    
    @overload
    def __init__(
        self,
        session: RequestManager,
        max_workers: int | None = None
    ) -> None: ...
    
    @overload
    def __init__(
        self,
        session: aiohttp.ClientSession,
        max_workers: int | None = None,
        **kwargs: Unpack[RequestItem]
    ) -> None: ...
    
    def __init__(
        self,
        session: RequestManager | aiohttp.ClientSession,
        max_workers: int | None = None,
        **kwargs
    ) -> None:
        if isinstance(session, RequestManager):
            self.session = session
        else:
            self.session = RequestManager(session, **kwargs)

        self.executer = ThreadPoolExecutor(max_workers = max_workers or self.BASE_MAX_WORKER)
        
    async def download(self, gallery: list[str] | MangaSchema, path: str | Path) -> Path:
        """Метод для скачивание фоток в PDF

        Args:
            gallery (list[str] | MangaSchema): URL-ы фоток или схема манги
            path (str | Path): путь для сохраниение (пример "manga.pdf")
        """
        if isinstance(gallery, MangaSchema):
            gallery = [str(x) for x in gallery.gallery]
        elif isinstance(gallery, list):
            gallery = gallery
        else:
            raise TypeError(
                f"Не поддерживаемый тип ({type(gallery).__name__})"
            )
            
        path = Path(path)
        if path.suffix.lower() != ".pdf":
            path = path.with_suffix(".pdf")
            logger.warning(
                f"Расширение не было указано, будет использован PDF файл (path={path})"
            )
        
        async with aiofiles.tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            
            saved_images: list[Path] = []
            tasks: list[asyncio.Task[bool]] = []
            
            for indx, url in enumerate(gallery):
                webp = tmp_path / f"{indx}.webp"
                tasks.append(asyncio.create_task(self._write(webp, url)))
                saved_images.append(webp)
                
            for task in asyncio.as_completed(tasks):
                result = await task
                if not result:
                    logger.warning(f"Не удалось скачать изображение")
                    continue
            
            images = await self._convert(saved_images)
            await self._build_pdf(images, path)
            
        return path
    
    async def _build_pdf(self, images: list[IMG], path: str | Path):
        """Создаёт PDF файл, в указанной директории

        Args:
            images (list[IMG]): фотки
            path (str | Path): путь для сохраниение
        """
        loop = asyncio.get_event_loop()
        img = images.pop(0)
        await loop.run_in_executor(
            self.executer,
            lambda: img.save(path, save_all=True, append_images=images)
        )

    async def _write(self, path: str, url: str):
        """Записывает webp в файл

        Args:
            path (str): путь для сохраниение
            url (str): URL фотки
        """
        async with aiofiles.open(path, "wb") as file:
            response = await self.session.get(url, 'read')
            if response is None:
                return False

            await file.write(response)
            return True
            
    async def _convert(self, images: list[str | Path]) -> list[IMG]:
        """Преобразует WEBP в PNG

        Args:
            images (list[str | Path]): фотки

        Returns:
            list[IMG]: фотки
        """
        def _convert(save_path):
            return Image.open(save_path).convert("RGB")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executer,
            lambda: [_convert(image) for image in images]
        )