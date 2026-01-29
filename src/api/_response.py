from typing import Generic, TypeVar
from pydantic import BaseModel, Field


_T = TypeVar("_T")


class BaseResponse(BaseModel, Generic[_T]):
    status: bool
    message: str
    
    result: _T | None = Field(default = None)