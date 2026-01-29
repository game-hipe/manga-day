from fastapi import APIRouter

from ...core.manager.manga import MangaManager
from ...core.entities.schemas import BaseManga
from .._response import BaseResponse

class Endpoints:
    def __init__(self, manga_manager: MangaManager):
        self.manga_manager = manga_manager
        self._router = APIRouter(
            prefix="/api/v1", tags=["api"]
        )
        
        self._setup_routes()
        
    def _setup_routes(self):
        self._router.add_api_route(
            "/pages/{page}",
            self.get_pages,
            methods=["GET"],
            response_model=BaseResponse[list[BaseManga]],
            summary="Получить список манги по страницам",
            tags=["manga"]
        )
        
    async def get_pages(self, page: int) -> BaseResponse[list[BaseManga] | None]:
        result = await self.manga_manager.get_manga_pages(page)
        try:
            return BaseResponse(
                status = True,
                message = f"Удалось достать {len(result)} манги",
                result = result
            )
            
        except Exception as e:
            return BaseResponse(
                status = False,
                message = f"Не удалось достать манги: {e}"
            )
            
    @property
    def router(self) -> APIRouter:
        return self._router