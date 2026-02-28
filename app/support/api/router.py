# app/support/api/router.py
import io

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import List
from dateutil.relativedelta import relativedelta
from fastapi import Depends, Query
from app.auth.dependencies import get_current_api_user
from app.core.config.project_config import settings, get_paging
from app.core.schemas.base import PaginatedResponse
# from app.mongodb import router as mongorouter
from app.core.config.database.db_async import get_db
from app.core.utils.common_utils import back_to_the_future, delta_data
from app.core.utils.converters import raw_image_response
# from app.mongodb.models import FileListResponse
from app.mongodb.service import ThumbnailImageService
from app.support.item.router import ItemRouter
from app.support.item.schemas import ItemApi
from app.support.api.service import ApiService
from app.support.item.repository import ItemRepository

delta = delta_data(settings.DATA_DELTA)
paging = get_paging


class ApiRouter(ItemRouter):
    def __init__(self):
        super().__init__(prefix='/api', auth_dependency=get_current_api_user)
        self.paginated_response = PaginatedResponse[ItemApi]
        self.nonpaginated_response = List[self.read_schema]
        self.repo = ItemRepository
        self.service = ApiService

    def setup_routes(self):
        self.router.add_api_route("", self.get, methods=["GET"],
                                  # get -> service.get_list_api_view_page -> repository.get_all
                                  response_model=PaginatedResponse[ItemApi],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/all", self.get_all, methods=["GET"],
                                  response_model=List[ItemApi],
                                  # response_model=List[self.read_schema],
                                  openapi_extra={'x-request-schema': None})
        # поиск api.service.search_geans -> core.repository.search_fts_all
        self.router.add_api_route("/search", self.search_geans, methods=["GET"],
                                  response_model=PaginatedResponse[ItemApi],
                                  openapi_extra={'x-request-schema': None}
                                  )
        # поиск api.search_geans_all -> core.repository.search_fts
        self.router.add_api_route("/search_all", self.search_geans_all,
                                  methods=["GET"],
                                  response_model=List[ItemApi],
                                  openapi_extra={'x-request-schema': None}
                                  )
        self.router.add_api_route("/get_by_ids", self.search_by_ids,
                                  methods=["GET"],
                                  response_model=List[ItemApi],
                                  openapi_extra={'x-request-schema': None}
                                  )
        """self.router.add_api_route("/mongo", self.get_images_after_date, methods=["GET"],
                                  response_model=FileListResponse,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/mongo_all", self.get_images_list_after_date, methods=["GET"],
                                  response_model=dict,
                                  openapi_extra={'x-request-schema': None})"""
        self.router.add_api_route("/{id}", self.get_api, methods=["GET"],
                                  response_model=ItemApi,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/image/{id}", self.get_image_by_id, methods=["GET"],
                                  openapi_extra={'x-request-schema': None},
                                  )
        self.router.add_api_route("/thumbnail/{id}", self.get_thumbnail_by_id, methods=["GET"],
                                  openapi_extra={'x-request-schema': None}, )
        self.router.add_api_route("/image_png/{id}", self.get_image_png_by_id, methods=["GET"],
                                  openapi_extra={'x-request-schema': None}, )
        self.router.add_api_route("/thumbnail_png/{id}", self.get_thumbnail_png_by_id, methods=["GET"],
                                  openapi_extra={'x-request-schema': None}, )

    async def get_images_after_date(
        self,
        after_date: datetime = Query(delta, description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"),
        page: int = Query(1, ge=1, description="Номер страницы"),
        per_page: int = Query(10, ge=1, le=1000, description="Количество элементов на страницу"),
        image_service: ThumbnailImageService = Depends()
    ):
        """
        Получение постраничного списка id изображений, созданных после заданной даты.
        по умолчанию за 2 года но сейчас
        """
        try:
            after_date = back_to_the_future(after_date)
            return await image_service.get_images_after_date(after_date, page, per_page)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def get_images_list_after_date(self, after_date: datetime = Query(delta,
                                                                            description="Дата в формате ISO "
                                                                                        "8601 (например, "
                                                                                        "2024-01-01T00:00:00Z)"),
                                         image_service: ThumbnailImageService = Depends()) -> dict:
        """
        список всех изображений в базе данных без страниц
        :return: возвращает список кортежей (id файла, имя файла)
        """
        try:
            # Проверяем, что дата не в будущем
            after_date = back_to_the_future(after_date)
            result = await image_service.get_images_list_after_date(after_date)
            return {a: b for b, a in result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def get_api(self, id: int, session: AsyncSession = Depends(get_db)) -> ItemApi:
        """
             Получение одной записи по id.
        """
        service = ApiService
        result = await service.get_item_api_view(id, session)
        return result

    async def get_all(self, after_date: datetime = Query(
        (datetime.now(timezone.utc) - relativedelta(years=2)).isoformat(),
        description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"
    ), session: AsyncSession = Depends(get_db)):
        """
            Получение всех записей одним списком после указанной даты.
            Может быть очень тяжелым запросом
        """
        try:
            after_date = back_to_the_future(after_date)
            service = ApiService
            repository = ItemRepository
            result = await service.get_list_api_view(after_date, repository, self.model, session)
            return result

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Internal server error. {e}")

    async def get(self,
                  after_date: datetime = Query(delta,
                                               description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"),
                  page: int = Query(1, ge=1),
                  page_size: int = Query(paging.get('def', 20),
                                         ge=paging.get('min', 1),
                                         le=paging.get('max', 1000)),
                  session: AsyncSession = Depends(get_db)
                  ) -> PaginatedResponse:
        """
            Получение постранично всех записей после заданной даты.
        """
        # print(f"📥 GET request for {self.model.__name__} from")
        after_date = back_to_the_future(after_date)
        service = ApiService
        response = await service.get_list_api_view_page(after_date, page, page_size, self.repo, self.model, session)
        result = self.paginated_response(**response)
        return result

    async def get_image_by_id(self, id: int, session: AsyncSession = Depends(get_db),
                              image_service: ThumbnailImageService = Depends()):
        """
            получение изображения по id напитка. Версия 1  (StreamingResponse)
        """
        image_data = await self.service.get_image_by_id(id, self.repo, self.model, session, image_service)
        headers = {"Content-Disposition": f"inline; filename={image_data['filename']}", "X-Image-Type": "full",
                   "X-File-Size": str(len(image_data["content"]))}
        if image_data.get("from_cache"):
            headers["X-Cache"] = "HIT"
        else:
            headers["X-Cache"] = "MISS"
        return StreamingResponse(
            io.BytesIO(image_data["content"]), media_type=image_data['content_type'], headers=headers
        )

    async def get_thumbnail_by_id(self, id: int, session: AsyncSession = Depends(get_db),
                                  image_service: ThumbnailImageService = Depends()):
        """
            получение thumbnail по id напитка. Версия 1 (StreamingResponse)
        """
        image_data = await self.service.get_thumbnail_by_id(id, self.repo, self.model, session, image_service)
        headers = {"Content-Disposition": f"inline; filename={image_data['filename']}", "X-Image-Type": "thumbnail",
                   "X-File-Size": str(len(image_data["content"]))}
        if image_data.get("from_cache"):
            headers["X-Cache"] = "HIT"
        else:
            headers["X-Cache"] = "MISS"
        return StreamingResponse(
            io.BytesIO(image_data["content"]), media_type=image_data['content_type'], headers=headers
        )

    async def get_image_png_by_id(self, id: int, session: AsyncSession = Depends(get_db),
                                  image_service: ThumbnailImageService = Depends()):
        """
        получение изображения по id напитка. Версия 2 (Response)
        """
        image_data = await self.service.get_image_by_id(id, self.repo, self.model, session, image_service)
        return raw_image_response(image_data)

    async def get_thumbnail_png_by_id(self, id: int, session: AsyncSession = Depends(get_db),
                                      image_service: ThumbnailImageService = Depends()):
        """
            получение thumbnail by id. Версия 2 (Response)
        """
        image_data = await self.service.get_thumbnail_by_id(id, self.repo, self.model, session, image_service)
        return raw_image_response(image_data)

    async def search_by_ids(self, search: str = Query(
            None, description="Поисковый запрос. В случае пустого запроса будут выведены все данные "
    ),
            session: AsyncSession = Depends(get_db)):
        """
            Получение записей по ids.
            Может быть очень тяжелым запросом
        """
        try:
            service = ApiService
            repository = ItemRepository
            result = await service.get_list_api_view_ids(search, repository, self.model, session)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)
