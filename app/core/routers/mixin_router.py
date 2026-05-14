# app.core.routers.mixin_router.py
"""
    mixins routers = добавлять после BaseRouter
    ItemRouter(BaseRouter, MixinRouter)
"""
from typing import Dict, Union

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repositories.array_repository import ArrayRepository
from app.core.services.array_service import ArrayService
from app.core.types import ModelType


class ArrayRouter:
    """
        эндпойнты для обработки полей с массивами
    """
    arrayName: str = 'seaweed_fids'  # default value.

    def setup_routes(self):
        """Маршруты из миксина"""
        # self.router.add_api_route("/mixin", self.mixin_endpoint, methods=["GET"],
        #                           openapi_extra={'x-request-schema': None})
        # Позволяет безопасно замыкать цепочку или вызывать другие миксины.
        # пути без параметров сверху super, c параметрами под супер
        self.router.add_api_route("/mixin/get/{id}", self.get_array_by_id, methods=["GET"],
                                  openapi_extra={'x-request-schema': None})
        next_method = getattr(super(), "setup_routes", None)
        if next_method:
            next_method()

    async def get_array_by_id(self, id: int, session: AsyncSession) -> Union[Dict, None]:
        service: ArrayService = self.service
        repository: ArrayRepository = self.repo
        model: ModelType = self.model
        arrayName = self.arrayName
        return await service.get_array_by_id(id, model, arrayName, repository, session)
