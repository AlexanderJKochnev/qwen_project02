# app.support.merging.router.py
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_active_user_or_internal
from app.support.merging.service import MergingService


class MergingRouter:
    def __init__(self):
        prefix = 'merging'
        self.tags, self.prefix = [f'{prefix}'], f'/{prefix}'
        self.router = APIRouter(
            prefix=self.prefix, tags=self.tags, dependencies=[Depends(get_active_user_or_internal)]
        )
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route(
            "", self.get_drinks_lwins, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/data", self.get_drinks_data, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )

    async def get_drinks_lwins(self, service: MergingService = Depends()) -> dict:
        """
        получение списка  fid изображений по странично / только для тестирования
        """
        response = await service.get_drinks_lwins()
        return {'result': response}

    async def get_drinks_data(self, service: MergingService = Depends()) -> dict:
        """

        """
        response = await service.get_drinks_data()
        return {'result': response}
