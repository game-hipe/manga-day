import datetime
from typing import Literal, Generic, TypeVar

from pydantic import BaseModel, Field


_T = TypeVar("_T")


class AlertMessage(BaseModel):
    """
    Схема сигнала для сообщение
    """

    message: str
    level: str


class StatusMessage(BaseModel):
    """
    Схема для получение пауков
    """

    name: str
    status: str
    message: str


class ParsingSignal(BaseModel):
    """
    Схема сигнала для парсинга
    """

    signal: Literal["start", "stop", "update"]
    spider: Literal["all"] | str

    page: int | None = Field(None)
    timeout: int = Field(10)


class BaseResponse(BaseModel, Generic[_T]):
    """
    Базовая схема ответа
    """

    status: bool
    signal: str
    result: _T | None = Field(default=None)


class MessageResponse(BaseResponse[AlertMessage]):
    """
    Схема ответа с сообщением
    """

    status: bool = Field(default=True)
    signal: str = Field(default="alert")


class SpiderResponse(BaseResponse[list[StatusMessage]]):
    """
    Схема ответа со статусом
    """

    status: bool = Field(default=True)
    signal: str = Field(default="status")


class AuthStatus(BaseModel):
    """
    Схема ответа для авторизации
    """

    user_name: str
    password: str
    iat: datetime.datetime
    exp: datetime.datetime
    token: str


class GetAlertMessage(AlertMessage):
    """
    Схема сигнала что-бы получить Alert
    """

    name: str | None = Field(None)
    """От кого было получено сообщение"""


class AlertSendResponse(BaseResponse[GetAlertMessage]):
    """
    Схема ответа для отправки Alert
    """

    message: str | None = Field(None)
    signal: str = Field("alert-response")
