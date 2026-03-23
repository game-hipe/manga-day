from urllib.parse import urljoin
from typing import overload, Unpack

import aiohttp

from loguru import logger

from ..abstract.request import RequestItem
from ..entities.schemas import MangaSchema, MangaWithGallery, OutputMangaSchema
from ..manager.request import RequestManager
from ..exc import CantDownloadImage


class PDFService:
    """
    Класс для преобразование фоток в PDF

    Основной метод:
        download(gallery, path) - Скачивает фотки, и сохраняет в виде PDF

    NOTE:
        В будущем можно добавить REDIS, для кэширование
    """

    BASE_MAX_IMAGES: int = 100
    """Базовое максимальное число изображений для скачивания"""

    ENDPOINT: str = "/generate-pdf"

    @overload
    def __init__(
        self,
        session: RequestManager,
        domen: str,
    ) -> None: ...

    @overload
    def __init__(
        self,
        session: aiohttp.ClientSession,
        domen: str,
        **kwargs: Unpack[RequestItem],
    ) -> None: ...

    def __init__(
        self,
        session: RequestManager | aiohttp.ClientSession,
        domen: str,
        **kwargs,
    ) -> None:
        if isinstance(session, RequestManager):
            self.session = session
        else:
            self.session = RequestManager(
                session, **kwargs, maxsize=1
            )  # Число 1 выбрано так-как кэш может "Съесть" всю память
        self.url = urljoin(domen, self.ENDPOINT)

    async def download(self, gallery: list[str] | MangaWithGallery) -> bytes | None:
        """Основной метод для скачивания изображений и сохранения в PDF.

        Args:
            gallery (list[str] | MangaSchema | OutputMangaSchema): Схема для манги с gallery, либо список ссылок на изображения.

        Returns:
            bytes: PDF файл в виде bytes
        """
        images_urls = self._extract_images(gallery)

        return await self.session.post(self.url, "read", json=images_urls)

    @staticmethod
    def _extract_images(gallery: list[str] | MangaWithGallery) -> list[str]:
        """Достать ссылки на изображение

        Args:
            gallery (list[str] | MangaSchema | OutputMangaSchema): Галлерея

        Raises:
            CantDownloadImage: Ошибка если не удалось достать ссылки

        Returns:
            list[str]: Список ссылок на изображения
        """
        result = None

        if isinstance(gallery, (MangaSchema, OutputMangaSchema)):
            result = [str(x) for x in gallery.gallery]

        if isinstance(gallery, list):
            if all(isinstance(x, str) for x in gallery):
                result = gallery

        if result:
            logger.debug(f"Удалось получить (urls_count={len(result)})")
            return result

        raise CantDownloadImage("Неверный тип данных для gallery")
