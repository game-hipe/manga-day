import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import pytest_asyncio
from aiohttp import ClientSession
from src.spider.hmanga import HmangaSpider
from src.spider.multi_manga import MultiMangaSpider

class TestSpiderMultiManga:
    @pytest.fixture
    def url(self):
        return "https://multi-manga.today/16126-moja-povsednevnaja-zhizn-s-sestroj-grjaznulej-kotoroj-nuzhen-tolko-seks-esli-pobedish-sestrenku-to-ja-razreshu-tebe-konchit-bez-rezinki-boku-to.html"
    
    @pytest.fixture
    def tags(self):
        return ['ahegao', 'x-ray', 'анал', 'анилингус', 'без трусиков', 'большая грудь', 'большие попки', 'вибратор', 'волосатые женщины', 'глубокий минет', 'групповой секс', 'инцест', 'кремпай', 'купальники', 'мастурбация', 'мать', 'мерзкий дядька', 'минет', 'молоко', 'обычный секс', 'огромная грудь', 'оплодотворение', 'сетакон', 'чулки', 'школьная форма', 'школьный купальник']
        
    @pytest_asyncio.fixture
    async def session(self):
        """Асинхронная фикстура для создания сессии"""
        async with ClientSession() as session:
            yield session
    
    @pytest_asyncio.fixture
    async def spider(self, session):
        """Асинхронная фикстура для создания паука"""
        return MultiMangaSpider(session)
    
    @pytest.mark.asyncio
    async def test_spider_get(self, spider):
        """Асинхронный тест"""
        
        result = await spider.http.get(
            "https://multi-manga.today", 'text'
        )
        if result is None:
            pytest.exit(
                "Не удалось соедениться с сайтом, возможно стоит включить VPN либо сменить домен."
            )
            
        assert result is not None
        
    @pytest.mark.asyncio
    async def test_spider_get_manga(self, spider, url):
        result = await spider.get(url)
        
        assert result is not None
        
    @pytest.mark.asyncio
    async def test_spider_get_title(self, spider, url):
        result = await spider.get(url)
        
        assert result.title == "Моя повседневная жизнь с сестрой-грязнулей, которой нужен только секс ~Если победишь сестрёнку, то я разрешу тебе кончить без резинки!~ (Boku to Gasatsu na Onee no Seiyoku Shori Seikatsu ~Onee-chan ni Katetara Ninshin Kakugo de Nama Ecchi Hen~)"

    @pytest.mark.asyncio
    async def test_spider_get_genres(self, spider, tags, url):
        result = await spider.get(url)
    
        for tag in tags:
            assert tag in result.genres
            
    @pytest.mark.asyncio
    async def test_spider_get_language(self, spider, url):
        result = await spider.get(url)

        assert result.language == "Русский"
        
    @pytest.mark.asyncio
    async def test_spider_get_poster(self, spider, url):
        result = await spider.get(url)
        
        assert str(result.poster) == "https://multi-manga.today/uploads/posts/2026-01/medium/1767914666_01.webp"
        
    @pytest.mark.asyncio
    async def test_spider_get_gallery(self, spider, url):
        result = await spider.get(url)
        
        assert len(result.gallery) == 36
        
    @pytest.mark.asyncio
    async def test_spider_get_author(self, spider, url):
        result = await spider.get(url)
        
        assert result.author == "Jovejun"
        
class TestSpiderHmanga:
    
    @pytest.fixture
    def url(self):
        return "https://hmanga.my/14674-hagure-moguri-ogaritai-hitozuma-kateikyoushi-musuko-to-danna-ga-inai-sabishii-seikatsu-o-okutteru-naraboku-no-mama-ni-natte-chinese.html"

    @pytest.fixture
    def tags(self):
        return ["Big Ass", "Big Breasts", "Cheating", "MILF", "Nakadashi", "Shotacon", "Sole Female", "Sole Male", "Tutor"]

    @pytest_asyncio.fixture
    async def session(self):
        """Асинхронная фикстура для создания сессии"""
        async with ClientSession() as session:
            yield session
    
    @pytest_asyncio.fixture
    async def spider(self, session):
        """Асинхронная фикстура для создания паука"""
        return HmangaSpider(session)
    
    @pytest.mark.asyncio
    async def test_spider_get(self, spider):
        """Асинхронный тест"""
        
        result = await spider.http.get(
            "https://hmanga.my", 'text'
        )
        if result is None:
            pytest.exit(
                "Не удалось соедениться с сайтом, возможно стоит включить VPN либо сменить домен."
            )
            
        assert result is not None
        
    @pytest.mark.asyncio
    async def test_spider_get_manga(self, spider, url):
        result = await spider.get(url)
        
        assert result is not None
        
    @pytest.mark.asyncio
    async def test_spider_get_title(self, spider, url):
        result = await spider.get(url)
        
        assert result.title == "[Hagure Moguri] Ogaritai Hitozuma Kateikyoushi ~Musuko to Danna ga Inai Sabishii Seikatsu o Okutteru Naraboku no Mama ni Natte~ [Chinese]"

    @pytest.mark.asyncio
    async def test_spider_get_genres(self, spider, tags, url):
        result = await spider.get(url)
    
        for tag in tags:
            assert tag in result.genres
            
    @pytest.mark.asyncio
    async def test_spider_get_language(self, spider, url):
        result = await spider.get(url)

        assert result.language == "chinese"
        
    @pytest.mark.asyncio
    async def test_spider_get_poster(self, spider, url):
        result = await spider.get(url)
        
        assert str(result.poster) == "https://hmanga.my/uploads/posts/2026-01/medium/1767911442_1.webp"
        
    @pytest.mark.asyncio
    async def test_spider_get_gallery(self, spider, url):
        result = await spider.get(url)
        
        assert len(result.gallery) == 38
        
    @pytest.mark.asyncio
    async def test_spider_get_author(self, spider, url):
        result = await spider.get(url)
        
        assert result.author is None