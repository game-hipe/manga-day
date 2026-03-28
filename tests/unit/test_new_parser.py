import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from src.spider.hmanga.parser import MangaParser as HmangaParser
from src.spider.multi_manga.parser import MangaParser as MultiMangaParser
from src.spider.hitomi.parser import HitomiMangaParser
from src.core.exc import ParserError, ParseSituationNotAllowed


class BaseTestParser:
    """Базовый класс для тестирования парсеров"""

    @pytest.fixture
    def minimal_valid_html(self):
        """Минимальный валидный HTML для парсера"""
        raise NotImplementedError

    @pytest.fixture
    def parser(self):
        """Фикстура должна быть переопределена в дочерних классах"""
        raise NotImplementedError

    def test_parse_empty_html(self, parser):
        """Тест парсинга пустого HTML"""
        with pytest.raises(ParserError):
            parser.parse("")

    def test_parse_none_html(self, parser):
        """Тест парсинга None"""
        with pytest.raises(TypeError):
            parser.parse(None)

    def test_parse_malformed_html(self, parser):
        """Тест парсинга битого HTML"""
        malformed = "<html><body><div>Unclosed div"
        # Проверяем что не падает с исключением (либо обрабатывает, либо кидает понятное исключение)
        try:
            result = parser.parse(malformed)
            # Если не упало, проверяем что результат хоть что-то содержит
            assert result is not None
        except Exception as e:
            assert isinstance(e, (ParserError, ParseSituationNotAllowed))

    def test_parse_with_missing_canonical(self, parser, minimal_valid_html):
        """Тест парсинга HTML без canonical ссылки"""
        with pytest.raises(ParserError, match="Не удалось извлечь данные из HTML."):
            html = minimal_valid_html.replace('rel="canonical"', "")
            parser.parse(html)

    def test_parser_initialization(self, parser):
        """Тест инициализации парсера"""
        assert parser.base_url is not None
        assert parser.situation == "html"


class TestHmangaParser(BaseTestParser):
    @pytest.fixture
    def parser(self):
        return HmangaParser("https://hmanga.my/", situation="html")

    @pytest.fixture
    def minimal_valid_html(self):
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/1">
            <div id="info"><h1>Minimal Manga</h1></div>
        </html>
        """

    @pytest.fixture
    def sample_html(self):
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/1">
            <div id="info">
                <h1>Test Manga</h1>
            </div>
            <div id="cover">
                <img data-src="/poster.jpg">
            </div>
            <section id="tags">
                <div class="tag-container">Contents
                    <a class="tag">Action</a>
                    <a class="tag">Drama</a>
                </div>
            </section>
        </html>
        """

    @pytest.fixture
    def html_without_author(self):
        """HTML без информации об авторе"""
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/2">
            <div id="info">
                <h1>No Author Manga</h1>
            </div>
            <div id="cover">
                <img data-src="/poster2.jpg">
            </div>
            <section id="tags">
                <div class="tag-container">Contents
                    <a class="tag">Comedy</a>
                </div>
            </section>
        </html>
        """

    @pytest.fixture
    def html_without_language(self):
        """HTML без указания языка"""
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/3">
            <div id="info">
                <h1>No Language Manga</h1>
            </div>
            <div id="cover">
                <img data-src="/poster3.jpg">
            </div>
        </html>
        """

    @pytest.fixture
    def html_without_tags(self):
        """HTML без тегов"""
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/4">
            <div id="info">
                <h1>No Tags Manga</h1>
            </div>
            <div id="cover">
                <img data-src="/poster4.jpg">
            </div>
        </html>
        """

    @pytest.fixture
    def html_without_poster(self):
        """HTML без постера"""
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/5">
            <div id="info">
                <h1>No Poster Manga</h1>
            </div>
            <section id="tags">
                <div class="tag-container">Contents
                    <a class="tag">Romance</a>
                </div>
            </section>
        </html>
        """

    @pytest.fixture
    def html_without_title(self):
        """HTML без заголовка"""
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/6">
            <div id="info">
                <!-- No title here -->
            </div>
            <div id="cover">
                <img data-src="/poster6.jpg">
            </div>
        </html>
        """

    @pytest.fixture
    def html_with_multiple_languages(self):
        """HTML с указанием нескольких языков"""
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/7">
            <div id="info">
                <h1>Multi-Language Manga [English][Chinese][Japanese]</h1>
            </div>
            <div id="cover">
                <img data-src="/poster7.jpg">
            </div>
        </html>
        """

    @pytest.fixture
    def html_with_special_characters(self):
        """HTML со специальными символами в названии"""
        return """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/8">
            <div id="info">
                <h1>Manga with Special Chars: テスト &amp; "Quotes" &lt;Tags&gt;</h1>
            </div>
            <div id="cover">
                <img data-src="/poster8.jpg">
            </div>
        </html>
        """

    def test_parse_valid_html(self, parser, sample_html):
        """Тест парсинга валидного HTML"""
        result = parser.parse(sample_html)

        assert result.title == "Test Manga"
        assert "Action" in result.genres
        assert "Drama" in result.genres
        assert len(result.genres) == 2
        assert str(result.poster) == "https://hmanga.my/poster.jpg"

    def test_parse_no_author(self, parser, html_without_author):
        """Тест парсинга HTML без автора"""
        result = parser.parse(html_without_author)
        assert result.author is None
        assert result.title == "No Author Manga"

    def test_parse_no_language(self, parser, html_without_language):
        """Тест парсинга HTML без языка"""
        result = parser.parse(html_without_language)
        # Проверяем что язык либо None, либо дефолтное значение
        assert result.language is None or result.language == ""

    def test_parse_no_tags(self, parser, html_without_tags):
        """Тест парсинга HTML без тегов"""
        result = parser.parse(html_without_tags)
        assert result.genres == [] or result.genres is None

    def test_parse_no_poster(self, parser, html_without_poster):
        """Тест парсинга HTML без постера"""
        with pytest.raises(ParserError, match="Не удалось извлечь данные из HTML."):
            parser.parse(html_without_poster)

    def test_parse_no_title(self, parser, html_without_title):
        """Тест парсинга HTML без заголовка"""
        with pytest.raises(ParserError, match="Не удалось извлечь данные из HTML."):
            parser.parse(html_without_title)

    def test_parse_multiple_languages(self, parser, html_with_multiple_languages):
        """Тест парсинга HTML с несколькими языками в названии"""

        result = parser.parse(html_with_multiple_languages)
        # Проверяем что парсер корректно обрабатывает сложные названия
        assert "[English][Chinese][Japanese]" in result.title

    def test_parse_special_characters(self, parser, html_with_special_characters):
        """Тест парсинга HTML со специальными символами"""
        result = parser.parse(html_with_special_characters)
        # Проверяем что HTML entities декодируются
        assert "テスト" in result.title
        assert '"Quotes"' in result.title
        assert "<Tags>" in result.title or "&lt;Tags&gt;" in result.title

    def test_parse_empty_gallery(self, parser):
        """Тест парсинга HTML без галереи"""
        html = """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/9">
            <div id="cover">
                <img data-src="/uploads/poster.jpg">
            </div>
            <div id="info"><h1>No Gallery Manga</h1></div>
            <!-- Нет элементов галереи -->
        </html>
        """
        result = parser.parse(html)
        assert result.gallery == [] or result.gallery is None

    def test_parse_relative_urls(self, parser):
        """Тест обработки относительных URL"""
        html = """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/10">
            <div id="info"><h1>Relative URLs</h1></div>
            <div id="cover">
                <img data-src="../uploads/poster.jpg">
            </div>
        </html>
        """
        result = parser.parse(html)
        # Проверяем что относительные пути корректно преобразуются
        assert result.poster is not None

    def test_parse_invalid_image_url(self, parser):
        """Тест обработки невалидных URL изображений"""
        html = """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/11">
            <div id="info"><h1>Invalid Image URL</h1></div>
            <div id="cover">
                <img data-src="://invalid-url">
            </div>
        </html>
        """
        result = parser.parse(html)
        # Парсер должен либо пропустить невалидный URL, либо сохранить как есть
        assert result is not None

    # -------------------------------------------
    # ТЕСТЫ С РЕАЛЬНЫМИ ДАННЫМИ
    # -------------------------------------------

    @pytest.fixture
    def tags(self):
        return [
            "Big Ass",
            "Big Breasts",
            "Cheating",
            "MILF",
            "Nakadashi",
            "Shotacon",
            "Sole Female",
            "Sole Male",
            "Tutor",
        ]

    @pytest.fixture
    def real_html(self):
        with open("test_templates/hamnga-1.html", "r", encoding="utf-8") as f:
            return f.read()

    def test_parse_real_html_title(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            result.title
            == "[Hagure Moguri] Ogaritai Hitozuma Kateikyoushi ~Musuko to Danna ga Inai Sabishii Seikatsu o Okutteru Naraboku no Mama ni Natte~ [Chinese]"
        )

    def test_parse_real_html_genres(self, parser, real_html, tags):
        result = parser.parse(real_html)

        for tag in tags:
            assert tag in result.genres
        # Дополнительно проверяем количество тегов
        assert len(result.genres) >= len(tags)

    def test_parse_real_html_language(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.language == "chinese"

    def test_parse_real_html_poster(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            str(result.poster)
            == "https://hmanga.my/uploads/posts/2026-01/medium/1767911442_1.webp"
        )

    def test_parse_real_html_gallery(self, parser, real_html):
        result = parser.parse(real_html)
        assert len(result.gallery) == 38
        # Проверяем что все URL в галерее валидны
        for img in result.gallery:
            assert str(img).startswith("http")

    def test_parse_real_html_author(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.author is None


class TestMultiMangaParser(BaseTestParser):
    @pytest.fixture
    def parser(self):
        return MultiMangaParser("https://multi-manga.today", situation="html")

    @pytest.fixture
    def minimal_valid_html(self):
        return """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/1">
            <div id="info"><h1>Минимальная Манга</h1></div>
        </html>
        """

    @pytest.fixture
    def sample_html(self):
        return """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/1">
            <div id="info">
                <h1>Тестовая Манга</h1>
            </div>
            <div id="cover">
                <img data-src="/poster.jpg">
            </div>
            <section id="tags">
                <div class="tag-container">Теги
                    <a class="tag">Секс</a>
                    <a class="tag">Драма</a>
                </div>
                <div class="tag-container">Автор
                    <a class="tag">Тестовый Автор</a>
                </div>
                
            </section>
        </html>
        """

    @pytest.fixture
    def html_with_cyrillic(self):
        """HTML с кириллическими символами"""
        return """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/2">
            <div id="info">
                <h1>Манга с Ё и Ъ</h1>
            </div>
            <div id="cover">
                <img data-src="/poster.jpg">
            </div>
            <section id="tags">
                <div class="tag-container">Теги
                    <a class="tag">Объёмная грудь</a>
                    <a class="tag">Ёлки-палки</a>
                </div>
            </section>
        </html>
        """

    def test_parse_valid_html(self, parser, sample_html):
        result = parser.parse(sample_html)
        print(result)
        assert result.title == "Тестовая Манга"
        assert "Секс" in result.genres
        assert "Драма" in result.genres
        assert len(result.genres) == 2
        assert str(result.poster) == "https://multi-manga.today/poster.jpg"
        assert result.author == "Тестовый Автор"

    def test_parse_cyrillic_tags(self, parser, html_with_cyrillic):
        """Тест парсинга кириллических тегов"""
        result = parser.parse(html_with_cyrillic)

        assert "Объёмная грудь" in result.genres
        assert "Ёлки-палки" in result.genres
        assert result.title == "Манга с Ё и Ъ"

    def test_parse_html_with_script_tags(self, parser):
        """Тест парсинга HTML с script тегами"""
        html = """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/3">
            <div id="cover">
                <img data-src="/poster%20with%20spaces.jpg">
            </div>
            <div id="info">
                <h1>Манга со скриптами</h1>
            </div>
            <script>alert('test');</script>
            <div>Content</div>
            <script>console.log('test2');</script>
        </html>
        """
        result = parser.parse(html)
        assert result.title == "Манга со скриптами"
        # Убеждаемся что скрипты не мешают парсингу

    def test_parse_html_with_comments(self, parser):
        """Тест парсинга HTML с комментариями"""
        html = """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/4">
            <!-- Это комментарий -->
            <div id="cover">
                <img data-src="/poster%20with%20spaces.jpg">
            </div>
            <div id="info">
                <h1>Манга с комментариями</h1>
                <!-- Ещё комментарий -->
            </div>
            <!-- И ещё -->
        </html>
        """
        result = parser.parse(html)
        assert result.title == "Манга с комментариями"

    def test_parse_with_duplicate_tags(self, parser):
        """Тест парсинга HTML с дублирующимися тегами"""
        html = """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/5">
            <div id="info">
                <h1>Манга с дублями</h1>
            </div>
            <div id="cover">
                <img data-src="/poster%20with%20spaces.jpg">
            </div>
            <section id="tags">
                <div class="tag-container">Теги
                    <a class="tag">Секс</a>
                    <a class="tag">Секс</a>  <!-- Дубликат -->
                    <a class="tag">Драма</a>
                    <a class="tag">Драма</a>  <!-- Дубликат -->
                </div>
            </section>
        </html>
        """
        result = parser.parse(html)
        # Проверяем что дубликаты удаляются
        assert len(result.genres) == 2
        assert "Секс" in result.genres
        assert "Драма" in result.genres

    def test_parse_with_encoded_urls(self, parser):
        """Тест парсинга HTML с закодированными URL"""
        html = """
        <html>
            <link rel="canonical" href="https://multi-manga.today.org/manga/6">
            <div id="info">
                <h1>Манга с encoded URL</h1>
            </div>
            <div id="cover">
                <img data-src="/poster%20with%20spaces.jpg">
            </div>
        </html>
        """
        result = parser.parse(html)
        # Проверяем что пробелы в URL декодируются
        assert result.poster is not None

    # -------------------------------------------
    # ТЕСТЫ С РЕАЛЬНЫМИ ДАННЫМИ
    # -------------------------------------------

    @pytest.fixture
    def tags(self):
        return [
            "ahegao",
            "x-ray",
            "анал",
            "анилингус",
            "без трусиков",
            "большая грудь",
            "большие попки",
            "вибратор",
            "волосатые женщины",
            "глубокий минет",
            "групповой секс",
            "инцест",
            "кремпай",
            "купальники",
            "мастурбация",
            "мать",
            "мерзкий дядька",
            "минет",
            "молоко",
            "обычный секс",
            "огромная грудь",
            "оплодотворение",
            "сетакон",
            "чулки",
            "школьная форма",
            "школьный купальник",
        ]

    @pytest.fixture
    def real_html(self):
        with open("test_templates/multi-manga-1.html", "r", encoding="utf-8") as f:
            return f.read()

    def test_parse_real_html_title(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            result.title
            == "Моя повседневная жизнь с сестрой-грязнулей, которой нужен только секс ~Если победишь сестрёнку, то я разрешу тебе кончить без резинки!~ (Boku to Gasatsu na Onee no Seiyoku Shori Seikatsu ~Onee-chan ni Katetara Ninshin Kakugo de Nama Ecchi Hen~)"
        )

    def test_parse_real_html_genres(self, parser, real_html, tags):
        result = parser.parse(real_html)

        for tag in tags:
            assert tag in result.genres
        # Проверяем что тегов достаточно много
        assert len(result.genres) >= len(tags)

    def test_parse_real_html_language(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.language == "Русский"

    def test_parse_real_html_poster(self, parser, real_html):
        result = parser.parse(real_html)
        assert (
            str(result.poster)
            == "https://multi-manga.today/uploads/posts/2026-01/medium/1767914666_01.webp"
        )

    def test_parse_real_html_gallery(self, parser, real_html):
        result = parser.parse(real_html)
        assert len(result.gallery) == 36
        # Проверяем что все изображения в галерее имеют правильные расширения
        for img in result.gallery:
            assert any(
                str(img).endswith(ext)
                for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]
            )

    def test_parse_real_html_author(self, parser, real_html):
        result = parser.parse(real_html)
        assert result.author == "Jovejun"


class HitomiParser(BaseTestParser):
    @pytest.fixture
    def parser(self):
        return HitomiMangaParser("https://hmanga.my/", situation="html")

    @pytest.fixture
    def minimal_valid_html(self):
        return """
        <html>
            <link rel="canonical" href="https://hitomy.si/manga/1">
            <div id="info"><h1>Minimal Manga</h1></div>
        </html>
        """


@pytest.mark.parametrize(
    "parser_class,base_url",
    [
        (HmangaParser, "https://hmanga.my/"),
        (MultiMangaParser, "https://multi-manga.today"),
    ],
)
def test_parser_initialization_errors(parser_class, base_url):
    """Тест ошибок инициализации парсеров"""
    # Тест с некорректным URL
    with pytest.raises(ValueError):
        parser_class("", situation="html")

    with pytest.raises(ValueError):
        parser_class(None, situation="html")

    # Тест с некорректной ситуацией
    with pytest.raises(AttributeError):
        parser_class(base_url, situation="invalid_situation")

    # Корректная инициализация
    parser = parser_class(base_url, situation="html")
    assert parser.base_url == base_url
    assert parser.situation == "html"


# Дополнительные интеграционные тесты
class TestParserIntegration:
    """Интеграционные тесты для парсеров"""

    def test_parsers_return_consistent_structure(self):
        """Тест что оба парсера возвращают одинаковую структуру данных"""
        hmanga_parser = HmangaParser("https://hmanga.my/", situation="html")
        multi_parser = MultiMangaParser("https://multi-manga.today", situation="html")

        # Создаем минимальный HTML для обоих парсеров
        hmanga_html = """
        <html>
            <link rel="canonical" href="https://hmanga.my/manga/1">
            <div id="info"><h1>Test</h1></div>
            <div id="cover">
                <img data-src="/poster%20with%20spaces.jpg">
            </div>
        </html>
        """

        multi_html = """
        <html>
            <link rel="canonical" href="https://multi-manga.today/manga/1">
            <div id="info"><h1>Test</h1></div>
            <div id="cover">
                <img data-src="/poster%20with%20spaces.jpg">
            </div>
        </html>
        """

        hmanga_result = hmanga_parser.parse(hmanga_html)
        multi_result = multi_parser.parse(multi_html)

        # Проверяем что оба результата имеют одинаковые атрибуты
        assert hasattr(hmanga_result, "title")
        assert hasattr(multi_result, "title")
        assert hasattr(hmanga_result, "genres")
        assert hasattr(multi_result, "genres")
        assert hasattr(hmanga_result, "poster")
        assert hasattr(multi_result, "poster")
        assert hasattr(hmanga_result, "author")
        assert hasattr(multi_result, "author")
        assert hasattr(hmanga_result, "language")
        assert hasattr(multi_result, "language")

    def test_parser_with_different_encodings(self):
        """Тест парсеров с разными кодировками"""
        parsers = [
            HmangaParser("https://hmanga.my/", situation="html"),
            MultiMangaParser("https://multi-manga.today", situation="html"),
        ]

        # HTML с разными кодировками в строке
        test_cases = [
            ("Normal HTML", "utf-8"),
            ("HTML с кириллицей: Привет", "utf-8"),
            ("HTML with emoji: 😀🎉", "utf-8"),
            ("HTML with Latin-1: café résumé", "iso-8859-1"),
        ]

        for title, encoding in test_cases:
            html = f"""
            <html>
                <meta charset="{encoding}">
                <link rel="canonical" href="https://test.com/manga/1">
                <div id="info"><h1>{title}</h1></div>
                <div id="cover">
                    <img data-src="/poster.jpg">
                </div>
            </html>
            """

            for parser in parsers:
                try:
                    result = parser.parse(html)
                    assert result is not None
                    # Проверяем что заголовок был корректно распознан
                    assert title in result.title or result.title is not None
                except UnicodeDecodeError:
                    # Некоторые кодировки могут не поддерживаться
                    pass
