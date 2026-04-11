import asyncio
import os
from urllib.parse import urlparse

from loguru import logger

from src import start_user
from src import start_admin
from src.core.api import API
from src.core.pdf import PDFmanager
from src.core.alert import AlertManager, AdminAPI

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
PROXY = os.getenv("PROXY")
API_URL = os.getenv("API_URL")
SITE_URL = os.getenv("SITE_URL")
PDF_URL = os.getenv("PDF_URL")
ADMIN_IDS = os.getenv("ADMIN_IDS")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


if not ADMIN_BOT_TOKEN and not USER_BOT_TOKEN:
    logger.critical(
        "Не указан ни один токен бота. Пожалуйста, укажите токен в переменных окружения."
    )
    raise ValueError(
        "Не указан ни один токен бота. Пожалуйста, укажите токен в переменных окружения."
    )


async def main():
    user_api = API(API_URL)
    admin_api = AdminAPI(user_api._session, API_URL, ADMIN_USERNAME, ADMIN_PASSWORD)
    alert = AlertManager(admin_api, f"ws://{urlparse(API_URL).netloc}/v1/api/admin/ws")
    pdf = PDFmanager(user_api._session, PDF_URL)

    async with user_api as api:
        async with asyncio.TaskGroup() as tg:
            if USER_BOT_TOKEN:
                tg.create_task(
                    start_user(
                        api=api,
                        pdf=pdf,
                        alert=alert,
                        token=USER_BOT_TOKEN,
                        proxy=PROXY,
                        site=SITE_URL,
                    )
                )
            if ADMIN_BOT_TOKEN:
                tg.create_task(
                    start_admin(
                        admin_api,
                        alert,
                        token=ADMIN_BOT_TOKEN,
                        proxy=PROXY,
                        admin_ids=[int(x) for x in ADMIN_IDS.split(",")]
                        if ADMIN_IDS
                        else [],
                    )
                )
            tg.create_task(alert.start_listening())


try:
    asyncio.run(main())

except KeyboardInterrupt:
    logger.info("Бот остановлен пользователем.")

except Exception as e:
    logger.critical(f"Произошла ошибка: {e}")
    raise

finally:
    logger.info("Бот остановлен.")
