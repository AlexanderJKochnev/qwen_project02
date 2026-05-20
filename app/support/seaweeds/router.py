# app.core.support.seaweeds.router.py
from fastapi import File, HTTPException, Query, UploadFile
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.utils.io_utils import ResponseJust, ResponseStreaming
from app.core.config.database.db_async import get_db
from app.auth.dependencies import get_active_user_or_internal
from app.core.services.seaweed_service import SeaweedsService
from app.mongodb.service import ThumbnailImageService

"""
    all bellow routes for the test purpose only
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
            "/search_fids", self.search_by_tag, methods=["GET"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/search_image", self.search_image_by_fid,
            methods=["GET"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.get, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/transfer", self.transfer_mongoo_sea,
            methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/{fid}", self.get_by_fid, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/direct/{fid}", self.get_direct_by_fid, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.create_img, methods=["POST"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "test", self.test_create_img, methods=["POST"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "", self.delete_img, methods=["DELETE"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/thumb/{fid}",
            self.get_thumb, methods=["GET"], openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/thumb_image/{fid}", self.get_thumb_by_fid, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )

    async def create_img(self,
                         description: str = Query(..., description='ключевые слова по которым можно найти '
                                                  'изображение'),
                         table_name: str = Query('items', description='имя таблицы для которой '
                                                                      'предназначено изображение. items'),
                         content_type: int = Query(0, description='возвращает результат: 0 - ничего, '
                                                             '1 - полное изображение, 2 - thumbnail'),
                         processor_type: int = Query(4, description='выбор процессора'),
                         file: UploadFile = File(...),
                         service: SeaweedsService = Depends()):
        try:
            content = await file.read()
            # response: (meta, content | None)
            meta, content = await service.create_img(content, description, table_name, content_type, processor_type)
            if content:
                kwargs = {key: val for key, val in meta.items() if key in ('fid', 'fid_thumb')}
                if isinstance(content, list):
                    content = content[-1]
                return ResponseStreaming(content, **kwargs)
            else:
                return meta
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=e)

    async def delete_img(self, fid: str,
                         table_name: str = Query('items', description='имя таблицы для которой '
                                                 'предназначено изображение. items'
                                                 ),
                         service: SeaweedsService = Depends()) -> dict:
        """
            удаление изображения
        """
        await service.delete_img(fid, table_name)
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

    async def get_by_fid(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение изображения по fid
        """
        image_data: bytes = await service.get_image(fid)
        return ResponseStreaming(image_data)
        # return StreamingResponse(**image_data)

    async def get_thumb_by_fid(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение thum изображения
        """
        image_data: bytes = await service.get_thumb_by_fid(fid)
        return ResponseStreaming(image_data)

    async def get_thumb(self, fid: str, service: SeaweedsService = Depends()):
        """
        получение fid, fid_thumb by fid
        """
        response = await service.get_fid_thumb(fid)
        return response

    async def get_direct_by_fid(self, fid: str, service: SeaweedsService = Depends()) -> bytes:
        """
        получение изображения по fid напрямую из seaweed
        """
        image_data: bytes = await service.get_direct_image(fid)
        return ResponseJust(image_data)

    async def search_by_tag(self, tag_value: str, service: SeaweedsService = Depends()):
        """
        получение fid изображения по tag
        """
        result: dict = await service.search_fid_by_tag(tag_value)
        return result
        # return StreamingResponse(**image_data)

    async def search_image_by_fid(self, tag_value: str,
                                  image_type: int = Query(1, description='1: полное изображениеб 2: thumbnail'),
                                  service: SeaweedsService = Depends()):
        """
        получение изображения по tag
        """
        image_data: bytes = await service.search_image_by_tag(tag_value, image_type)
        return ResponseStreaming(image_data)
        # return StreamingResponse(**image_data)

    async def transfer_mongoo_sea(self, session: AsyncSession = Depends(get_db),
                                  service: SeaweedsService = Depends(),
                                  image_service: ThumbnailImageService = Depends()):
        # перенос (копирование) файлов из mongodb в seaweed, запись fid в items.seaweed_fids[0]
        # запускать только один раз
        # response = await service.get_items_pairs(session, image_service)
        # запись в items.seaweed_fids[1] thumbnails fids
        # response = await service.transfer_tier2(session, image_service)
        # новый encoder webp
        response = await service.transfer_tier3(session, image_service)
        return response

    async def test_create_img(self,
                              file: UploadFile = File(...),
                              dimension: int = Query(1000,
                                                     description='максимальный размер в который нужно вписать '
                                                                 'изображение, pix'),
                              size: int = Query(100, description='максимальный размер файла, Kb'),
                              quality: int = Query(85, description='качество изображениия 100 самое лучшее, 0 плохое'),
                              type: int = Query(1,
                                                description='1. PNG, 2. WEBP OLD, 3. WEBP LOSSLESS, '
                                                            '4. WEBP LOSSY, 5. WEBP LOSSY BATCH'),
                              full: bool = Query(True, description='True полное, False thumbnail'),
                              service: SeaweedsService = Depends()):
        """
             загрузка обработка и возврат изображеня БЕЗ сохранения - для оценки качества обработки
        """
        from app.core.utils.hashes import FastImageHasher
        content = await file.read()
        source_hash = FastImageHasher.xxhash64(content)
        original_size = len(content)
        logger.info(f'{original_size=}')
        image_data = await service.test_create_img(content, dimension, size, type, quality, full)
        return ResponseStreaming(image_data, source_size=original_size, xxhash=source_hash)
