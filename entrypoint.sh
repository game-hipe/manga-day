#!/bin/sh

# Ждем, пока PostgreSQL станет доступен
echo "Waiting for PostgreSQL..."
while ! nc -z manga-postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Запускаем миграции
echo "Running migrations..."
alembic upgrade head

# Запускаем основное приложение
echo "Starting application..."
exec python main.py
