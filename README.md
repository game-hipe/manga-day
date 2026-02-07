![logo](https://raw.githubusercontent.com/game-hipe/manga-day/refs/heads/main/src/frontend/user/static/images/logo.png)

# Manga-Day Новая манга в 2 клика!
В чём суть проекта? У меня есть много сайтов, где манга выходит не каждый день, но следит за ними нужно, поэтому я подумал почему-бы не просто создать пауков, и ТГ админку? Вот на этом и решили!

## На будущее!
Стоит улучшить API, для полноценности проекта, так-же улучшить Бота на стороне пользователя!

## Как запустить проект?
```bash
git clone https://github.com/game-hipe/manga-day.git
cd manga-day
cp config-example.yaml config.yaml

nano config.yaml # Вставтье ваш бот токен, для работы.

docker-compose build --no-cache
docker-compose up -d
```

## 2 Способ через прямой python (python3.14.X+)
```bash
git clone https://github.com/game-hipe/manga-day.git
cd manga-day
cp config-example.yaml config.yaml

nano config.yaml # Вставтье ваш бот токен, для работы.
pip install -r requirements.txt
python main.py
```

> [!WARNING]
> Донор данных hitomi, была добавлена защита Cloudflare, поэтому на данный момента паук "hitomi" не доступен.


## Структура проекта

```text
└── ./
    ├── .github
    │   └── workflows
    │       └── python-app.yml
    ├── src
    │   ├── api
    │   │   ├── handlers
    │   │   │   ├── __init__.py
    │   │   │   └── endpoints.py
    │   │   ├── __init__.py
    │   │   ├── _api.py
    │   │   └── _response.py
    │   ├── bot
    │   │   ├── handlers
    │   │   │   ├── __init__.py
    │   │   │   └── commands.py
    │   │   ├── middleware
    │   │   │   ├── __init__.py
    │   │   │   └── admins.py
    │   │   ├── __init__.py
    │   │   ├── _alert.py
    │   │   ├── _bot.py
    │   │   └── _text.py
    │   ├── core
    │   │   ├── abstract
    │   │   │   ├── alert.py
    │   │   │   ├── parser.py
    │   │   │   └── spider.py
    │   │   ├── entities
    │   │   │   ├── models.py
    │   │   │   └── schemas.py
    │   │   ├── manager
    │   │   │   ├── __init__.py
    │   │   │   ├── manga.py
    │   │   │   ├── request.py
    │   │   │   └── spider.py
    │   │   ├── service
    │   │   │   └── manga.py
    │   │   ├── __init__.py
    │   │   ├── _config.py
    │   │   └── _cron.py
    │   ├── frontend
    │   │   ├── admin
    │   │   │   ├── handlers
    │   │   │   │   └── __init__.py
    │   │   │   ├── static
    │   │   │   │   ├── css
    │   │   │   │   │   └── style.css
    │   │   │   │   └── js
    │   │   │   │       └── script.js
    │   │   │   ├── templates
    │   │   │   │   └── index.html
    │   │   │   ├── __init__.py
    │   │   │   └── _alert.py
    │   │   ├── templates
    │   │   │   └── 404.html
    │   │   ├── user
    │   │   │   ├── handlers
    │   │   │   │   └── __init__.py
    │   │   │   ├── static
    │   │   │   │   └── css
    │   │   │   │       ├── 404.css
    │   │   │   │       ├── base.css
    │   │   │   │       ├── gallery.css
    │   │   │   │       └── manga.css
    │   │   │   ├── templates
    │   │   │   │   ├── 404.html
    │   │   │   │   ├── base.html
    │   │   │   │   ├── index.html
    │   │   │   │   ├── manga.html
    │   │   │   │   └── not_found.html
    │   │   │   └── __init__.py
    │   │   ├── __init__.py
    │   │   └── _frontend.py
    │   ├── spider
    │   │   ├── base_spider
    │   │   │   ├── __init__.py
    │   │   │   ├── parser.py
    │   │   │   └── spider.py
    │   │   ├── hitomi
    │   │   │   ├── __init__.py
    │   │   │   ├── parser.py
    │   │   │   └── spider.py
    │   │   ├── hmanga
    │   │   │   ├── __init__.py
    │   │   │   ├── parser.py
    │   │   │   └── spider.py
    │   │   ├── multi_manga
    │   │   │   ├── __init__.py
    │   │   │   ├── parser.py
    │   │   │   └── spider.py
    │   │   └── __init__.py
    │   └── __init__.py
    ├── tests
    │   └── unit
    │       ├── test_database.py
    │       ├── test_manga_manager.py
    │       ├── test_new_parser.py
    │       ├── test_parsers.py
    │       ├── test_service.py
    │       └── test_spider.py
    ├── .dockerignore
    ├── .gitignore
    ├── config-example.yaml
    ├── docker-compose.yaml
    ├── Dockerfile
    ├── main.py
    ├── optional-requirements.txt
    ├── README.md
    └── requirements.txt

```

> [!WARNING]
> Проект является просто демонстрацие своих сил в BackEnd, и в ТГ ботах, поэтому не бейте тапком
