# app.core.support.seaweeds.router.py
from fastapi import File, HTTPException, Query, UploadFile
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
from app.core.utils.io_utils import ResponseStreaming, ResponseJust
from app.auth.dependencies import get_active_user_or_internal
from app.core.services.seaweed_service import SeaweedsService

"""
    create
    search
    get
    get_by_id
    delete
    update
"""


class SeaweedsRouter:
    def __init__(self):
        prefix = 'seaweeds'
        self.tags, self.prefix = [f'{prefix}'], f'/{prefix}'
        self.router = APIRouter(
            prefix=self.prefix, tags=self.tags, dependencies=[Depends(get_active_user_or_internal)]
        )
        # self.service: SeaweedsService = Depends()
        self.setup_routes()
        # super().__init__(prefix='/seaweeds')

    def setup_routes(self):
        self.router.add_api_route(
            "", self.get, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/{id}", self.get_by_id, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.create_img, methods=["POST"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.delete_img, methods=["DELETE"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/thumb/{id}",
            self.get_thumb, methods=["GET"], openapi_extra={'x-request-schema': None}
        )

    async def create_img(self,
                         description: str = Query(..., description='ключевые слова по которым можно найти '
                                                  'изображение'),
                         table_name: str = Query(..., description='имя таблицы для которой '
                                                                  'предназначено изображение. items/...'),
                         file: UploadFile = File(...),
                         service: SeaweedsService = Depends()):
        try:
            content = await file.read()
            response: dict = await service.create_img(content, description, table_name)
            return response
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=e)

    async def delete_img(self, fid: str, service: SeaweedsService = Depends()) -> dict:
        """
            удаление изображения
        """
        await service.delete_img(fid)
        return {'fid': fid,
                'result': 'deleted'}

    async def get(self,
                  page: int = Query(1, description='страница'),
                  page_size: int = Query(1, description='размер страницы страница'),
                  # include_deleted: bool = Query(False, description='включить удаленные записи?'),
                  order_by: str = Query('inserted_at DESC', description='порядок сортировки '),
                  service: SeaweedsService = Depends()
                  ) -> dict:
        """
        получение списка  fid изображений по странично / только для тестирования
        """
        response = await service.get(page, page_size, order_by)
        return response

    async def get_by_id(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение изображения
        """
        image_data: dict = await service.get_image(fid)
        headers = image_data.pop('headers')
        return ResponseStreaming(image_data, headers)
        # return StreamingResponse(**image_data)
        

    async def get_thumb(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение fid, fid_thumb by fid
        """
        response = await service.get_fid_thumb(fid)
        return response
