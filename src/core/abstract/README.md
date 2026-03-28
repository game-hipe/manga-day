# Что такое `abstract`

Этот документ создан для личного использования, чтобы не забывать назначение абстрактных классов в проекте.

## Основные абстрактные классы

### 1. Базовый обработчик уведомлений
**Путь:** `/manager/abstract/alert.py`

Базовый класс для отправки уведомлений. Обязательный метод — `alert`.

```python
LEVEL: TypeAlias = Literal["info", "warning", "error", "critical"]

class BaseAlert:
    async def alert(self, message: str, level: LEVEL) -> bool:
        """
        Отправляет уведомление.

        Args:
            message (str): Текст сообщения.
            level (LEVEL): Уровень важности — "info", "warning", "error" или "critical".

        Returns:
            bool: True, если уведомление успешно отправлено. 
                  Если возвращает False, система уведомлений будет удалена.
        """
```

### 2. Базовые классы для парсинга
Путь: /manager/abstract/parser.py

Абстрактные классы для парсинга данных в разных форматах. Обязательные методы: _parse_html, _parse_json.

```python
class BaseParser:
    """Базовый парсер с поддержкой различных форматов."""

    @abstractmethod
    def _parse_html(self, soup: BeautifulSoup) -> Any:
        """Парсит HTML-разметку."""

    @abstractmethod
    def _parse_json(self, data: Any) -> Any:
        """Парсит JSON-данные."""


class BaseMangaParser(BaseParser[MangaSchema]):
    """Базовый класс для парсинга данных о манге."""


class BasePageParser(BaseParser[list[BaseManga]]):
    """Базовый класс для парсинга страниц с мангой."""
```

### 3. Базовый менеджер HTTP-запросов
**Путь:**: `/manager/abstract/request.py`

Универсальный класс для выполнения HTTP-запросов. Использует дженерики для типизации ответа.

```python
class BaseRequestManager(Generic[_T]):
    """Менеджер для выполнения HTTP-запросов."""
4. Базовый паук (spider)
Путь: /manager/abstract/spider.py

Абстрактный класс для реализации пауков, собирающих данные о манге. Обязательные методы: get, pages.

Python
class BaseSpider:
    @abstractmethod
    async def get(self, url: str, **kwargs) -> Optional[MangaSchema]:
        """
        Получает данные о манге по указанному URL.

        Args:
            url (str): Ссылка на страницу манги.
            **kwargs: Дополнительные параметры запроса.

        Returns:
            MangaSchema | None: Объект с данными о манге или None при ошибке.
        """

    @abstractmethod
    async def pages(
        self, start_page: int | None = None
    ) -> AsyncGenerator[list[BaseManga], Any]:
        """
        Асинхронно генерирует списки манги с последовательных страниц.

        Args:
            start_page (int | None): Номер начальной страницы. 
                                     Если None — начинает с первой.

        Yields:
            Списки объектов типа BaseManga.
        """
```