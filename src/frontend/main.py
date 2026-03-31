import os
import asyncio

from loguru import logger

from _frontend import start_frontend
from _dataclass import UrlParams

FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "8000")

API_URL = os.getenv("API_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8080")

url = UrlParams(API_URL=API_URL, BACKEND_PORT=BACKEND_PORT)


async def main():
    await start_frontend(
        frontend_host=FRONTEND_HOST, frontend_port=FRONTEND_PORT, url_params=url
    )


if __name__ == "__main__":
    try:
        logger.info("Запуск программы")
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем.")

    finally:
        logger.info("Программа завершила работу")
