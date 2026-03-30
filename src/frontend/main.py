import os
import asyncio

from _frontend import start_frontend


FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "8000")

API_URL = os.getenv("API_URL")

if API_URL is None:
    raise ValueError("API_URL не задан.")


async def main():
    await start_frontend(
        frontend_host=FRONTEND_HOST, frontend_port=FRONTEND_PORT, api_url=API_URL
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Программа прервана пользователем.")
