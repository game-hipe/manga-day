from typing import TypedDict, Literal
from dataclasses import dataclass, field

from loguru import logger


class UrlRules(TypedDict):
    use_type: Literal["api_url", "port"]
    value: str


@dataclass
class UrlParams:
    API_URL: str | None = field(default=None)
    BACKEND_PORT: str | None = field(default=None)

    __USE_TYPE: str = field(init=False)

    def __post_init__(self):
        if not self.API_URL and not self.BACKEND_PORT:
            logger.error("Необходимо указать хотя бы один из API_URL или BACKEND_PORT.")
            raise ValueError(
                "Необходимо указать хотя бы один из API_URL или BACKEND_PORT."
            )

        if self.API_URL:
            logger.debug(f"Используется API_URL: {self.API_URL}")
            self.__USE_TYPE = "api_url"

        else:
            logger.debug(f"Используется BACKEND_PORT: {self.BACKEND_PORT}")
            self.__USE_TYPE = "port"

    @property
    def use_rules(self) -> UrlRules:
        return {
            "use_type": self.__USE_TYPE,
            "value": self.API_URL if self.API_URL else self.BACKEND_PORT,
        }
