from pydantic import BaseModel


class SpiderStatus(BaseModel):
    name: str
    status: str
    message: str | None
    
    def __str__(self) -> str:
        return f"[<b>{self.name}</b>] - <b>{self.status}</b>" + f" | {self.message}" if self.message else ""
