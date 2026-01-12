# app/support/api/router.py
import io
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from dateutil.relativedelta import relativedelta
from fastapi import Depends, Query, Path
from app.core.utils.common_utils import back_to_the_future
from app.core.config.project_config import settings
from app.core.schemas.base import PaginatedResponse
from app.mongodb import router as mongorouter
from app.mongodb.models import FileListResponse
from app.mongodb.service import ImageService
from app.support.item.router import ItemRouter


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
        from app.core.utils.pydantic_utils import PyUtils
        self.paginated_response = PyUtils.paginated_response(self.read_schema)
        self.nonpaginated_response = PyUtils.non_paginated_response(self.read_schema)

    def setup_routes(self):
        # self.router.add_api_route("", self.get, methods=["GET"], response_model=self.paginated_response)
        self.router.add_api_route("", self.get, methods=["GET"],
                                  response_model=self.paginated_response,
                                  openapi_extra={'request_model': None})
        self.router.add_api_route("/all", self.get_all, methods=["GET"],
                                  response_model=self.nonpaginated_response,
                                  openapi_extra={'request_model': None})
        # self.router.add_api_route("/all", self.get_all, methods=["GET"], response_model=self.nonpaginated_response)
        self.router.add_api_route("/search", self.search, methods=["GET"],
                                  response_model=self.paginated_response,
                                  openapi_extra={'request_model': None})
        # self.router.add_api_route("/search_all", self.search_all, methods=["GET"],
        #                           response_model=List[self.read_schema])
        self.router.add_api_route("/search_all", self.search_all, methods=["GET"],
                                  response_model=self.nonpaginated_response,
                                  openapi_extra={'request_model': None})
        self.router.add_api_route("/mongo", self.get_images_after_date, methods=["GET"],
                                  response_model=FileListResponse,
                                  openapi_extra={'request_model': None})
        self.router.add_api_route("/mongo_all", self.get_images_list_after_date, methods=["GET"],
                                  response_model=dict,
                                  openapi_extra={'request_model': None})
        self.router.add_api_route("/{id}", self.get_one, methods=["GET"],
                                  response_model=self.read_schema,
                                  openapi_extra={'request_model': None})
        self.router.add_api_route("/mongo/{id}", self.download_image, methods=["GET"],
                                  openapi_extra={'request_model': None})
        self.router.add_api_route("/file/{file}", self.download_file, methods=["GET"],
                                  openapi_extra={'request_model': None})

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
