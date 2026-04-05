from urllib.parse import urljoin

import aiohttp
from cachetools import TTLCache
from aiogram.types import InputFile
from aiogram.types.input_file import DEFAULT_CHUNK_SIZE

from .schemas import Manga


class PDF(InputFile):
    def __init__(
        self,
        manga: Manga,
        pdf: "PDFmanager",
        filename=None,
        chunk_size=DEFAULT_CHUNK_SIZE,
    ):
        self.filename = (filename or manga.title) + ".pdf"
        self.chunk_size = chunk_size
        self.pdf = pdf
        self._manga = manga

    async def read(self, bot):
        async with self.pdf.session.request(
            method=self.pdf.METHOD,
            url=self.pdf.pdf_url,
            headers=self.pdf.headers,
            json=[str(x) for x in self._manga.gallery],
        ) as response:
            async for chunk in response.content.iter_chunked(self.chunk_size):
                yield chunk


class PDFmanager:
    ENDPOINT = "/generate-pdf"
    METHOD = "POST"

    MAX_SIZE = 8192
    TTL = 86400

    BASE_MAX_IMAGES = 100

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        headers: dict | None = None,
        max_size: int = MAX_SIZE,
        ttl: float = TTL,
    ):
        self._session = session
        self.base_url = base_url
        self.headers = headers or {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "MangaDay-Bot",
        }

        self._cache = TTLCache(maxsize=max_size, ttl=ttl)

    def get_pdf(self, manga: Manga) -> PDF | str:
        if file_id := self._cache.get(manga.sku):
            return file_id

        return PDF(manga, self)

    def set_pdf(self, manga: Manga | str, file_id: str) -> None:
        self._cache[self._get_sku(manga)] = file_id

    @staticmethod
    def _get_sku(manga: Manga | str) -> str:
        return manga.sku if isinstance(manga, Manga) else manga

    @property
    def pdf_url(self) -> str:
        return urljoin(self.base_url, self.ENDPOINT)

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session
