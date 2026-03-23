FROM python:3.11-slim

# Запрещаем Python писать .pyc файлы и буферизировать stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

# Установка зависимостей без кэширования для уменьшения размера образа
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Запуск. Дополнительно можно ограничить воркеры uvicorn, т.к. упор на экономию RAM (1 worker = ~40MB RAM в простое)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3040", "--workers", "1"]