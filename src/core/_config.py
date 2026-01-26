import sys

from loguru import logger
from pydantic import BaseModel, Field
from yaml import full_load


__all__ = [
    "config"
]

CONFIG_FILE = "config.yaml"

class LoggingConfig(BaseModel):
    level: str = Field("INFO")
    file_level: str = Field("INFO")
    file: str = Field("var/logs.log")
    
    format: str = Field("{time:YYYY-MM-DD HH:mm} | {level} | {message}")
    rotation: str = Field("10 MB")

class DataBaseConfig(BaseModel):
    db: str

class UpdateConfig(BaseModel):
    start_time: str = Field("7:00 AM")
    zone: str = Field(default="Asia/Yakutsk")

class BotConfig(BaseModel):
    api_key: str

class Config(BaseModel):
    logging: LoggingConfig
    update: UpdateConfig
    bot: BotConfig
    database: DataBaseConfig

def load_config():
    with open(CONFIG_FILE, "r") as f:
        config = Config(
            **full_load(f)
        )
        
    logger.remove()
    logger.add(
        config.logging.file,
        level = config.logging.file_level,
        format = config.logging.format,
        rotation = config.logging.rotation
    )
    logger.add(
        sys.stderr,
        level = config.logging.level,
        format = config.logging.format
    )
    
    logger.info("Конфигурация успешно загружена!")
    
    return config
        
config = load_config()