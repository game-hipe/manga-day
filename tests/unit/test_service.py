import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from src.core.manager.manga import MangaManager
from src.core.service.manga import FindService
from src.core.entities.models import Manga
from src.core.entities.schemas import MangaSchema, BaseManga


db_path = "test_templates/test-service-database.db"
mangas_path = "test_templates/mangas.json"


class TestService:
    @pytest_asyncio.fixture(scope="session")
    async def engine(self):
        """Создание асинхронного движка для тестовой БД"""

        if os.path.exists(db_path):
            os.remove(db_path)

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Manga.metadata.create_all)

            yield engine

        finally:
            await engine.dispose()
            if os.path.exists(db_path):
                os.remove(db_path)

    @pytest_asyncio.fixture
    async def database(self, engine):
        return MangaManager(engine)

    @pytest.fixture
    def mangas(self):
        result = []
        with open(mangas_path, encoding="utf-8") as f:
            for manga in json.load(f):
                result.append(MangaSchema(**manga))

        return result

    @pytest.fixture
    def service(self, database):
        return FindService(database)

    @pytest.fixture
    def manga_data(self):
        return MangaSchema(
            title="Test Manga",
            poster="https://example.com/poster.jpg",
            url="https://example.com/manga/1",
            sku="manga_001",
            genres=["ahegao", "simple sex"],
            author="Test Author",
            language="English",
            gallery=[
                "https://example.com/gallery/1.jpg",
                "https://example.com/gallery/2.jpg",
            ],
        )

    @pytest.mark.asyncio
    async def test_add(self, database, mangas):
        for manga in mangas:
            await database.add_manga(manga)

    @pytest.mark.asyncio
    async def test_find(self, service):
        mangas = await service.get_pages_by_query(
            "секс",  # Title,
            1,  # Page
        )

        assert len(mangas.response) == 6
        assert mangas.page == 1

    @pytest.mark.asyncio
    async def test_find_genre(self, service):
        mangas = await service.get_pages_by_genre(
            1,  # Genre ID
            1,  # PAGE
        )

        assert len(mangas.response) == 30
        assert mangas.page == 4

    @pytest.mark.asyncio
    async def test_find_author(self, service):
        mangas = await service.get_pages_by_author(
            27,  # Author ID
            1,  # PAGE
        )

        assert len(mangas.response) == 1
        assert mangas.page == 1

    @pytest.mark.asyncio
    async def test_find_language(self, service):
        mangas = await service.get_pages_by_language(
            1,  # Language ID
            1,  # PAGE
        )

        assert len(mangas.response) == 30
        assert mangas.page == 4

    @pytest.mark.asyncio
    async def test_check_error(self, service):
        with pytest.raises(ValueError):
            await service.get_pages_by_query(
                "",  # Title,
                1,  # Page
            )

        with pytest.raises(ValueError):
            await service.get_pages_by_query(
                "Секс",  # Title,
                0,  # Page
            )

        with pytest.raises(ValueError):
            await service.get_pages_by_genre(
                1,  # Genre ID
                1,  # PAGE
                -1,
            )

    @pytest.mark.asyncio
    async def test_get_manga_pages(self, service, manga_data):
        """Тест пагинации манги"""
        # Добавим несколько манг
        for i in range(1, 5):
            md = manga_data.model_copy(
                update={
                    "title": f"Test Manga {i}",
                    "sku": f"manga_00{i}",
                    "url": f"https://example.com/manga/{i}",
                }
            )
            await service.manager.add_manga(md)

        mangas = await service.get_pages(page=1, per_page=2)
        assert mangas.page == 52
        assert len(mangas.response) == 2
        assert all(isinstance(m, BaseManga) for m in mangas.response)

    @pytest.mark.asyncio
    async def test_get_manga_pages_invalid_page(self, service):
        """Тест ошибки при неверном номере страницы"""
        with pytest.raises(ValueError, match="Неверное число"):
            await service.get_pages(page=0)

    @pytest.mark.asyncio
    async def test_get_manga_pages_invalid_per_page(self, service):
        """Тест ошибки при неверном per_page"""
        with pytest.raises(ValueError, match="Неверное число"):
            await service.get_pages(page=1, per_page=0)
