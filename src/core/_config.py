import os
import sys

from loguru import logger
from pydantic import BaseModel, Field
from yaml import full_load

from dotenv import load_dotenv

__all__ = ["config"]

load_dotenv()

CONFIG_FILE = os.getenv("CONFIG_FILE", "config.yaml")


class RequestConfig(BaseModel):
    max_concurrents: int = Field(5)
    max_retries: int = Field(5)
    sleep_time: float = Field(2)
    use_random: bool = Field(True)
    maxsize: int = Field(100)
    ttl: float = Field(300)
    max_chance: int = Field(3)
    ban_proxy: bool = Field(True)


class ParserConfig(BaseModel):
    features: str = Field(
        "html.parser"
    )  # Рекемендуется использовать "lxml" для лучшей производительности, но он требует установки дополнительной библиотеки.
    proxy: list[str] = Field(default_factory=list)


class PDFConfig(BaseModel):
    save_path: str = Field("var/pdf")


class ApiConfig(BaseModel):
    frontend_port: int = Field(8000)
    backend_port: int = Field(8080)

    frontend_host: str = Field("0.0.0.0")
    backend_host: str = Field("0.0.0.0")


class LoggingConfig(BaseModel):
    level: str = Field("INFO")
    file_level: str = Field("INFO")
    file: str = Field("var/logs.log")

    format: str = Field(
        "<green>{time:YYYY-MM-DD HH:mm}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    rotation: str = Field("10 MB")


class DataBaseConfig(BaseModel):
    db: str = Field(os.getenv("DATABASE_URL"))


class UpdateConfig(BaseModel):
    start_time: str = Field("7:00 AM")
    zone: str = Field(default="Asia/Yakutsk")


class BotConfig(BaseModel):
    api_key: str = Field(os.getenv("USER_TOKEN"))
    url: str


class AdminBotConfig(BaseModel):
    api_key: str = Field(os.getenv("ADMIN_TOKEN"))
    admins: list[int]


class Config(BaseModel):
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    update: UpdateConfig = Field(default_factory=UpdateConfig)
    bot: AdminBotConfig
    user_bot: BotConfig
    database: DataBaseConfig = Field(default_factory=DataBaseConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    pdf: PDFConfig = Field(default_factory=PDFConfig)
    parsing: ParserConfig = Field(default_factory=ParserConfig)
    request: RequestConfig = Field(default_factory=RequestConfig)


def load_config():
    with open(CONFIG_FILE, "r") as f:
        config = Config(**full_load(f))

    logger.remove()
    logger.add(
        config.logging.file,
        level=config.logging.file_level,
        format=config.logging.format,
        rotation=config.logging.rotation,
    )
    logger.add(sys.stderr, level=config.logging.level, format=config.logging.format)

    logger.info("Конфигурация успешно загружена!")

    if config.parsing.features != "lxml":
        logger.warning(
            "Вы используете парсер 'html.parser', который может работать медленнее, чем 'lxml'. Рекомендуется установить 'lxml' для лучшей производительности."
        )

    try:
        os.mkdir(config.pdf.save_path)
    except FileExistsError:
        pass

    return config


config = load_config()
