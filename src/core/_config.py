# mypy: ignore-errors

import os
import sys
import warnings

from loguru import logger
from pydantic import BaseModel, Field, model_validator
from yaml import full_load

from dotenv import load_dotenv

__all__ = ["config"]

load_dotenv("api.env")

CONFIG_FILE = os.getenv("CONFIG_FILE", "config.yaml")


class AdminConfig(BaseModel):
    username: str = Field("admin")
    password: str = Field("admin")
    secret_key: str = Field(
        "supersecretadminkey1234567890abcdefgxyz!@#$_SECRET_KEY_LONGER_THAN_32_CHARS"
    )

    @model_validator(mode="after")
    def check_secret_key(self):
        if len(self.secret_key) < 32:
            warnings.warn(
                f"Длина секретного кода {len(self.secret_key)} "
                "менее 32 символам! "
                "Для более высокой безопасности рекомендуется более 32 символов".format(
                    len(self.secret_key)
                )
            )

        elif (
            self.secret_key
            == "supersecretadminkey1234567890abcdefgxyz!@#$_SECRET_KEY_LONGER_THAN_32_CHARS"
        ):
            warnings.warn(
                "Секретный ключ не изменен! "
                "Для более высокой безопасности рекомендуется изменить дефолтный"
            )

        return self


class RequestConfig(BaseModel):
    max_concurrent: int = Field(5)
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
    )  # Рекомендуется использовать "lxml" для лучшей производительности, но он требует установки дополнительной библиотеки.
    proxy: list[str] = Field(default_factory=list)


class ApiConfig(BaseModel):
    backend_port: int = Field(8080)
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
    db: str | None = Field(os.getenv("DATABASE_URL"))

    @model_validator(mode="after")
    def check_db(self):
        if self.db is None:
            raise ValueError(
                "Не указана переменная окружения DATABASE_URL, либо указанна неверно!"
            )

        return self


class UpdateConfig(BaseModel):
    start_time: str = Field(default="7:00 AM")
    zone: str = Field(default="Europe/Moscow")


class BotConfig(BaseModel):
    url: str


class Config(BaseModel):
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    update: UpdateConfig = Field(default_factory=UpdateConfig)
    user_bot: BotConfig
    database: DataBaseConfig = Field(default_factory=DataBaseConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    parsing: ParserConfig = Field(default_factory=ParserConfig)
    request: RequestConfig = Field(default_factory=RequestConfig)
    admin: AdminConfig = Field(default_factory=AdminConfig)


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

    if config.parsing.features != "lxml":
        logger.warning(
            "Вы используете парсер 'html.parser', который может работать медленнее, чем 'lxml'. Рекомендуется установить 'lxml' для лучшей производительности."
        )

    else:
        try:
            import lxml  # noqa
        except ImportError:
            logger.error(
                "Вы используете парсер 'lxml', который требует установки дополнительной библиотеки. Пожалуйста устоновите все зависимости из `requirements.txt` либо устоновите через `pip install lxml`"  # noqa
            )
            config.parsing.features = "html.parser"
            logger.warning("Используется парсер 'html.parser' вместо 'lxml'.")

    logger.info("Конфигурация успешно загружена!")

    if isinstance(config, Config):
        return config

    raise ValueError("Не удалось загрузить конфигурацию!")


config = load_config()
