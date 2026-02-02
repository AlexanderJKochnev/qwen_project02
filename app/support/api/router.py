# app/support/api/router.py
import io
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from dateutil.relativedelta import relativedelta
from fastapi import Depends, Query, Path
from app.core.utils.common_utils import back_to_the_future
from app.core.config.project_config import settings, get_paging
from app.core.schemas.base import PaginatedResponse
from app.mongodb import router as mongorouter
from app.core.config.database.db_async import get_db
from app.mongodb.models import FileListResponse
from app.mongodb.service import ImageService
from app.support.item.router import ItemRouter
from app.support.item.schemas import ItemApi
from app.support.item.service import ItemService
from app.support.item.repository import ItemRepository

delta = (datetime.now(timezone.utc) - relativedelta(years=2)).isoformat()
paging = get_paging


@dataclass
class Data:
    prefix: str
    delta: str
    mongo: str
    drink: str


data = Data(prefix=settings.API_PREFIX,
            delta=(datetime.now(timezone.utc) - relativedelta(years=2)).isoformat(),
            mongo='mongo',
            drink='drink'
            )


class ApiRouter(ItemRouter):
    def __init__(self):
        super().__init__(prefix='/api')
        # self.prefix = data.prefix
        # self.tags = data.prefix
        self.paginated_response = PaginatedResponse[ItemApi]
        self.nonpaginated_response = List[self.read_schema]

    def setup_routes(self):
        # self.router.add_api_route("", self.get, methods=["GET"], response_model=self.paginated_response)
        self.router.add_api_route("", self.get, methods=["GET"],
                                  # response_model=PaginatedResponse[self.read_schema],
                                  response_model=PaginatedResponse[ItemApi],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/all", self.get_all, methods=["GET"],
                                  response_model=List[ItemApi],
                                  # response_model=List[self.read_schema],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/search", self.search, methods=["GET"],
                                  response_model=self.paginated_response,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route(
            "/search_geans", self.search_geans, methods=["GET"], # response_model = self.paginated_response,
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route("/search_all", self.search_all, methods=["GET"],
                                  response_model=self.nonpaginated_response,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/mongo", self.get_images_after_date, methods=["GET"],
                                  response_model=FileListResponse,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/mongo_all", self.get_images_list_after_date, methods=["GET"],
                                  response_model=dict,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/{id}", self.get_api, methods=["GET"],
                                  response_model=ItemApi,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/mongo/{id}", self.download_image, methods=["GET"],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/file/{file}", self.download_file, methods=["GET"],
                                  openapi_extra={'x-request-schema': None})

    async def get_images_after_date(self, after_date: datetime = Query(data.delta, description="Дата в формате ISO "
                                                                                               "8601 (например, "
                                                                                               "2024-01-01T00:00:00Z)"),
                                    page: int = Query(1, ge=1, description="Номер страницы"),
                                    per_page: int = Query(100, ge=1, le=1000,
                                                          description="Количество элементов на странице"),
                                    image_service: ImageService = Depends()
                                    ):
        """
        Получение постраничного списка id изображений, созданных после заданной даты.
        по умолчанию за 2 года но сейчас
        """
        try:
            # Проверяем, что дата не в будущем
            after_date = back_to_the_future(after_date)
            return await image_service.get_images_after_date(after_date, page, per_page)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def get_images_list_after_date(self, after_date: datetime = Query(data.delta,
                                                                            description="Дата в формате ISO "
                                                                                        "8601 (например, "
                                                                                        "2024-01-01T00:00:00Z)"),
                                         image_service: ImageService = Depends()) -> dict:
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

    async def download_image(self,
                             file_id: str = Path(..., description="ID файла"),
                             image_service: ImageService = Depends()):
        """
            Получение одного изображения по _id
        """
        return await mongorouter.download_image(file_id, image_service)

    async def download_file(self,
                            filename: str = Path(..., description="Имя файла"),
                            image_service: ImageService = Depends()):
        """
            Получение одного изображения по имени файла
        """
        image_data = await image_service.get_image_by_filename(filename)

        return StreamingResponse(
            io.BytesIO(image_data["content"]), media_type=image_data['content_type'],
            headers={"Content-Disposition": f"attachment; filename={image_data['filename']}"}
        )

    async def get_api(self, id: int, session: AsyncSession = Depends(get_db)) -> ItemApi:
        """
             ItemApi
        """
        service = ItemService
        result = await service.get_item_api_view(id, session)
        return result

    async def get_all(self, after_date: datetime = Query(
        (datetime.now(timezone.utc) - relativedelta(years=2)).isoformat(),
        description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"
    ), session: AsyncSession = Depends(get_db)):
        """
            Получение всех записей одним списком после указанной даты.
            По умолчанию задана дата - 2 года от сейчас
            Очень тяжелый запрос
        """
        try:
            after_date = back_to_the_future(after_date)
            service = ItemService
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
            По умолчанию задана дата - 2 года от сейчас
            input_valudation_chema None
            response_model PaginatedResponse[<>ReadRelation>]
        """
        # print(f"📥 GET request for {self.model.__name__} from")
        after_date = back_to_the_future(after_date)
        service = ItemService
        response = await service.get_list_api_view_page(after_date, page, page_size, self.repo, self.model, session)
        result = self.paginated_response(**response)
        return result
