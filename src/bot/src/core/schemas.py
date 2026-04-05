from datetime import datetime

from typing import Literal

from pydantic import BaseModel, HttpUrl, Field, field_validator
from dateutil.parser import isoparse


LEVEL = Literal["info", "warning", "error", "critical"]


class ObjectWithId(BaseModel):
    name: str
    id: int


class BaseManga(BaseModel):
    id: int
    sku: str
    title: str
    poster: HttpUrl
    url: HttpUrl
    language: ObjectWithId | None = Field(None)
    author: ObjectWithId | None = Field(None)
    genres: list[ObjectWithId] = Field(default_factory=list)


class FindResult(BaseModel):
    query: str
    success: bool
    total: int
    page: int
    response: list[BaseManga] = Field(default_factory=list)


class Manga(BaseManga):
    gallery: list[HttpUrl] = Field(default_factory=list)


class LoginResponse(BaseModel):
    user_name: str
    password: str
    token: str

    iat: datetime
    exp: datetime

    @field_validator("iat", "exp", mode="before")
    @classmethod
    def parse_iso_date(cls, value: str) -> datetime:
        if isinstance(value, str):
            return isoparse(value)
        return value


class Alert(BaseModel):
    message: str
    level: LEVEL
    name: str


class AlertResponse(BaseModel):
    status: bool
    signal: Literal["alert-response"]
    result: Alert
    message: str


class SpiderStatus(BaseModel):
    name: str
    status: Literal[
        "success", "error", "processing", "not_running", "running", "cancelled"
    ]
    message: str | None

    def __str__(self):
        return f"<b>{self.name}</b> | {self.status} | {self.message}"
