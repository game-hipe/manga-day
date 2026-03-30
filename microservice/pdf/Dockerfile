FROM python:3.11-slim

# Запрещаем Python писать .pyc файлы и буферизировать stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

# Установка зависимостей без кэширования для уменьшения размера образа
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py health.py entrypoint.sh ./

RUN chmod +x /app/entrypoint.sh

# Запуск. Дополнительно можно ограничить воркеры uvicorn, т.к. упор на экономию RAM (1 worker = ~40MB RAM в простое)
ENTRYPOINT ["/app/entrypoint.sh"]
