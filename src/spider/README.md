# Как создать парсер что-бы он работал корректно?
Данный справочник создан по причине того что я сам начал забывать как создавать спайдеров (spiders) и я хочу себе-же создать `справочник`.

## Обшие действие
Эти методы, нужно создавать в обоих случаях
1. В папке `spider` создаём папку по типу `my_spider_example`

```bash
mkdir my_spider_example # Круто!
```

2. Создаём 3 файла `__init__.py`, `parser.py`, `spider.py`
```bash
touch __init__.py parser.py spider.py
```


## Способ 1: **с нуля**
Обший метод.
1. Заполняем `parser.py`
```python
from typing import Any

from ...core.abstract.parser import BaseMangaParser, BasePageParser
from ...core.entities.schemas import MangaSchema, BaseManga
from ...core.exc import ParserError, ParseSituationNotAllowed
from bs4 import BeautifulSoup


# Класс для парсинга манги
class ExampleMangaParser(BaseMangaParser):
    def _parse_html(self, soup: BeautifulSoup) -> MangaSchema:
        # Извлекаем название манги
        title = soup.select_one("h1")
        # Ищем постер по тегу img с классом poster
        poster = soup.select_one("img.poster")
        # Получаем канонический URL страницы
        url = soup.select_one('link[rel="canonical"]')

        # Проверяем, что все обязательные элементы найдены
        if not all([title, poster, url]):
            raise ParserError("Не удалось получить один из важных атрибутов")

        # Временные данные (можно заменить на реальный парсинг)
        genres = ["Фэнтези"]  # Жанры
        author = "Типо автор"  # Автор
        language = "Русский"  # Язык

        # Пример галереи (реальные ссылки на страницы)
        gallery = [
            "https://example.com/image/1",
            "https://example.com/image/2",
            "https://example.com/image/3"
        ]

        # Формируем объект с данными манги
        return MangaSchema(
            title=title.get_text(strip=True),   # Очищаем текст от пробелов
            poster=poster.get("src"),           # Берём ссылку на изображение
            url=url.get("href"),                # Атрибут href для link
            genres=genres,
            author=author,
            language=language,
            gallery=gallery
        )

    def _parse_json(self, data: Any) -> MangaSchema:
        # JSON-парсинг не поддерживается в этом парсере
        raise ParseSituationNotAllowed("Парсинг JSON не поддерживается")


# Класс для парсинга страниц
class ExamplePageParser(BasePageParser):
    def _parse_html(self, soup: BeautifulSoup) -> list[BaseManga]:
        items: list[BaseManga] = []

        # Перебираем элементы манги на странице
        for item in soup.select("div.mangas .manga"):  # Основной селектор контейнера
            title = item.get_text(strip=True)          # Извлекаем название
            poster = item.select_one("img")            # Находим постер
            url = item.select_one("a")                 # Получаем ссылку на мангу

            # Проверяем, что все данные присутствуют
            if all([title, poster, url]):
                items.append(
                    BaseManga(
                        title=title,
                        poster=poster.get("src"),      # Атрибут src изображения
                        url=url.get("href")            # Атрибут href ссылки
                    )
                )
        return items

    def _parse_json(self, data: Any) -> MangaSchema:
        # JSON-парсинг не поддерживается
        raise ParseSituationNotAllowed("Парсинг JSON не поддерживается")
```

2. Заполняем `spider.py`
```python
from typing import AsyncGenerator

from ...core.abstract.spider import BaseSpider # Импортируем базовый класс
from ...core.entities.schemas import MangaSchema
from .parser import ExampleMangaParser, ExamplePageParser

class ExampleSpider(BaseSpider): # Создаём наш класс

    BASE_URL = "https://example.com" # Указать реальный путь к URL

    def __init__(self, session, manager = None, features = None, batch = None, **kwargs):
        super().__init__(session, manager, features, batch, **kwargs)
        self.manga_parser = ExampleMangaParser(
            base_url = self.BASE_URL,
            features = self.features
        )
        self.page_parser = ExamplePageParser(
            base_url = self.BASE_URL,
            features = self.features
        )

    async def get(self, url: str, **kwargs):
        response = await self.http.get(url, 'read', **kwargs) # Можно read, text
        if response is None:
            return None # Если не удалось получить данные возвращаем ничего

        return self.manga_parser.parse(response)
        
    async def pages(
        self, start_page: int | None = None
    ) -> AsyncGenerator[list[BaseManga], None]:
        ... # Своя реализация

    @property
    def status(self): # Не обязательно но желательно
        return "23%"
```

> [!NOTE]  
> Необезательный атрибут `status` желательно чем либо заполнять

3. заполняем `__init__.py`
```python
from .spider import ExampleSpider

__all__ = [
    "ExampleSpider"
]
```

4. заполняем основной `__init__.py` по пути `src/spider/__init__.py`
```bash
from .hmanga import HmangaSpider
from .multi_manga import MultiMangaSpider
from .hitomi import HitomiSpider
from .hentaiera import HentaiEraSpider
from .moeimg import MoeImgSpider
from .porn_comic import PornComicSpider
from .my_spider_example import ExampleSpider

__all__ = [
    "HmangaSpider",
    "MultiMangaSpider",
    "HitomiSpider",
    "HentaiEraSpider",
    "MoeImgSpider",
    "PornComicSpider",
    "ExampleSpider"
]
```

> [!IMPORTANT]  
> Данный способ хорош тем-что вы управляете всем от А до Я, но нужно писать много retry кода


## Способ 2: **Использовать шаблон**

1. Заполняем `parser.py`
```python
# В данном примере будет показан код из паука `src/spider/multi_manga/parser.py`
from ..base_spider.parser import GlobalMangaParser, GlobalPageParser # Глобальные парсеры


class MangaParser(GlobalMangaParser):
    TAGS = {"теги": "genres", "автор": "author", "язык": "language"}


class PageParser(GlobalPageParser):
    SELECTOR = "div#dle-content div.gallery"

```

2. Заполняем `spider.py`
```python
# В данном примере будет показан код из паука `src/spider/multi_manga/spider.py`
from ..base_spider.spider import BaseMangaSpider # Загружаем общий метод
from .parser import MangaParser, PageParser # Загружаем !Кастомные! парсеры


class MultiMangaSpider(BaseMangaSpider):
    BASE_URL = "https://multi-manga.today"
    MANGA_PARSER = MangaParser
    PAGE_PARSER = PageParser

```

> [!WARNING]  
> В данном примере можно увидеть что, кода значительно меньше по причине того что base_spider создан для сайтов подобные multi-manga, так-же имеются шаблоны hitomy, ознакомиться с ними можете в `src/spider/hitomi`

> [!WARNING]  
> Ни один из примеров не рабочий и если вы хотите создать кастомного паука желательно знать базовый python, и [Beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

> [!TIP]
> Для глубины рекомендуестся иследовать `src/spider/base_spider` 


### Удачи! В создании самого удобного спайдера!