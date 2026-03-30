import asyncio
import logging
import os
import tempfile
import shutil
from typing import List

from fastapi import FastAPI, BackgroundTasks, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
import httpx
import img2pdf
from PIL import Image

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Отключаем Swagger/Redoc для экономии памяти
app = FastAPI(docs_url=None, redoc_url=None)


# --- ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ ОШИБОК ---
# Гарантируют возврат строгого HTTP 500 без тела при любой нештатной ситуации
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return Response(status_code=500)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc}")
    return Response(status_code=500)


MAX_CONCURRENT_DOWNLOADS = 5


async def download_image(
    client: httpx.AsyncClient, url: str, filepath: str, sem: asyncio.Semaphore
):
    """Асинхронное потоковое скачивание файла прямо на диск"""
    async with sem:
        logger.info(f"Downloading {url}")
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(filepath, "wb") as f:
                async for chunk in response.aiter_bytes(
                    chunk_size=65536
                ):  # Чанки по 64 КБ
                    f.write(chunk)


def prepare_image(filepath: str) -> str:
    """
    Подготовка файла. img2pdf встраивает JPEG/PNG без пережатия.
    Если формат другой (например, WEBP), мы последовательно конвертируем его,
    чтобы избежать загрузки всех изображений в RAM.
    """
    with Image.open(filepath) as img:
        fmt = img.format
        mode = img.mode

    # Если формат нативно поддерживается, оставляем как есть (zero-copy подход)
    if fmt in ["JPEG", "PNG", "JPEG2000"] and mode in ["RGB", "RGBA", "L", "1"]:
        return filepath

    # Последовательная конвертация для WEBP, BMP, GIF и т.д.
    logger.info(f"Converting unsupported format {fmt} for {filepath}")
    new_filepath = f"{filepath}_conv"

    with Image.open(filepath) as img:
        if img.mode in ("RGBA", "P", "LA"):
            new_filepath += ".png"
            img.save(new_filepath, "PNG")
        else:
            new_filepath += ".jpg"
            img = img.convert("RGB")
            img.save(new_filepath, "JPEG", quality=90)

    os.remove(filepath)  # Удаляем оригинал для экономии места на диске
    return new_filepath


def cleanup_temp_dir(path: str):
    """Удаление временной директории после отправки ответа клиенту"""
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
        logger.info(f"Cleaned up {path}")


@app.post("/generate-pdf")
async def generate_pdf(urls: List[str], background_tasks: BackgroundTasks):
    if not urls:
        return Response(status_code=500)

    # Создаем изолированную временную папку для текущего запроса
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "output.pdf")

    try:
        sem = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        limits = httpx.Limits(max_connections=MAX_CONCURRENT_DOWNLOADS)
        timeout = httpx.Timeout(30.0)

        filepaths = []

        # 1. Параллельное скачивание
        async with httpx.AsyncClient(
            limits=limits, timeout=timeout, proxy=os.getenv("PROXY")
        ) as client:
            tasks = []
            for idx, url in enumerate(urls):
                filepath = os.path.join(temp_dir, f"img_{idx:05d}")
                filepaths.append(filepath)
                tasks.append(download_image(client, url, filepath, sem))

            await asyncio.gather(*tasks)

        # 2. Подготовка изображений (Строго последовательно для защиты RAM)
        prepared_filepaths = []
        for fp in filepaths:
            prepared_filepaths.append(prepare_image(fp))

        # 3. Генерация PDF стримингом в файл (Без загрузки в оперативную память)
        with open(pdf_path, "wb") as f:
            img2pdf.convert(prepared_filepaths, outputstream=f)

        # 4. Отложенная очистка мусора после того, как клиент получит файл
        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        # FastAPI FileResponse стримит файл с диска чанками
        return FileResponse(path=pdf_path, media_type="application/pdf")

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        # При ошибке убираем за собой сразу
        cleanup_temp_dir(temp_dir)
        return Response(status_code=500)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
