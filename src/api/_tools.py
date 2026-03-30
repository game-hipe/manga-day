from ..core.manager import AuthManager
from fastapi import Header, Response, HTTPException, status


def auth_checker(auth: AuthManager):
    async def _auth_checker(
        response: Response,
        access_token: str | None = Header(None, alias="Authorization"),
    ):
        if access_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не был указан"
            )

        access_token = access_token.replace("Bearer ", "")

        if not auth.is_valid_token(access_token):
            response.delete_cookie("access_token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Неверный токен"
            )

        return access_token

    return _auth_checker
