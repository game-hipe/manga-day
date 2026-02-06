import os
import sys

from loguru import logger
from pydantic import BaseModel, Field
from yaml import full_load


__all__ = ["config"]

CONFIG_FILE = "config.yaml"


class PDFConfig(BaseModel):
    save_path: str = Field("var/pdf")


class ApiConfig(BaseModel):
    frontend_port: int = Field(8000)
    backend_port: int = Field(8080)


class LoggingConfig(BaseModel):
    level: str = Field("INFO")
    file_level: str = Field("INFO")
    file: str = Field("var/logs.log")

    format: str = Field(
        "<green>{time:YYYY-MM-DD HH:mm}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    rotation: str = Field("10 MB")


class DataBaseConfig(BaseModel):
    db: str


class UpdateConfig(BaseModel):
    start_time: str = Field("7:00 AM")
    zone: str = Field(default="Asia/Yakutsk")


class BotConfig(BaseModel):
    api_key: str


class AdminBotConfig(BotConfig):
    admins: list[int]


class Config(BaseModel):
    logging: LoggingConfig
    update: UpdateConfig
    bot: AdminBotConfig
    user_bot: BotConfig
    database: DataBaseConfig
    api: ApiConfig
    pdf: PDFConfig


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

    try:
        os.mkdir(config.pdf.save_path)
    except FileExistsError:
        pass

    return config


config = load_config()
