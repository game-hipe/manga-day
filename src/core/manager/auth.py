import jwt
from jwt.exceptions import PyJWTError

import datetime

from typing import TypedDict

from loguru import logger


class AuthDict(TypedDict):
    user_name: str
    password: str
    iat: datetime.datetime
    exp: datetime.datetime


class AuthToken(AuthDict):
    token: str


class AuthManager:
    """Менеджер авторизации."""

    ALGORITHM: str = "HS256"
    BASE_EXP = datetime.timedelta(minutes=15)

    def __init__(
        self,
        user_name: str,
        password: str,
        secret_key: str,
        base_exp: datetime.timedelta | None = None,
    ):
        """
        Менеджер авторизации.

        `НА ДАННЫЙ МОМЕНТ МОЖЕТ СУЩЕСТВОВАТЬ ТОЛЬКО 1 АДМИНИСТРАТОР`

        Args:
            user_name (str): Имя пользователя.
            password (str): Пароль.
            secret_key (str): Секретный ключ.
            base_exp (datetime.timedelta | None, optional): Время работы токена. По умолчанию None.
        """
        self.user_name = user_name
        self.password = password
        self.__secret_key = secret_key

        self.base_exp = base_exp or self.BASE_EXP

    def login(self, user_name: str, password: str) -> AuthToken | None:
        """Авторизация пользователя.

        Args:
            user_name (str): Имя пользователя.
            password (str): Пароль.

        Returns:
            str | None: Токен.
        """
        if user_name == self.user_name and password == self.password:
            payload = {
                "user_name": user_name,
                "password": password,
                "iat": datetime.datetime.now(datetime.timezone.utc),
                "exp": self._expire(),
            }
            return payload.copy() | {
                "token": jwt.encode(
                    payload=payload, key=self.password, algorithm=self.ALGORITHM
                )
            }

        return None

    def is_valid_token(self, token: str) -> bool:
        """Проверяет полученный токен.

        Args:
            token (str): Токен.

        Returns:
            bool: True если токен валидный. False иначе.
        """
        try:
            user: AuthDict = jwt.decode(token, self.password, algorithms=["HS256"])
            if user.get("user_name") != self.user_name:
                return False
            if user.get("password") != self.password:
                return False

            return True

        except PyJWTError as e:
            logger.debug(e)
            return False

    def _expire(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc) + self.base_exp

    @property
    def secret_key(self):
        return self.__secret_key
