# app/support/drink/router.py
import json

from fastapi import Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
# from app.core.config.project_config import settings
from app.core.utils.exception_handler import ValidationError_handler
from app.core.routers.base import BaseRouter
from app.mongodb.service import ImageService
from app.support.drink.drink_food_repo import DrinkFoodRepository
from app.support.drink.drink_food_service import DrinkFoodService
from app.support.drink.model import Drink
from app.support.drink.schemas import (DrinkCreate, DrinkCreateRelation, DrinkCreateResponseSchema,
                                       DrinkFoodLinkUpdate, DrinkRead, DrinkReadApi, DrinkUpdate,
                                       )
# from app.support.drink.service import DrinkService
# from app.support.drink.repository import DrinkRepository


class DrinkRouter(BaseRouter):
    def __init__(self, prefix: str = '/drinks'):
        self.read_api_schema = DrinkReadApi
        super().__init__(
            model=Drink,
            prefix=prefix)
        # self.image_service: ImageService = Depends()

    def setup_routes(self):
        super().setup_routes()
        # то что ниже удалить - было нужно до relation
        self.router.add_api_route("/{id}/foods", self.update_drink_foods,
                                  methods=["PATCH"],
                                  openapi_extra={'request_model': DrinkFoodLinkUpdate})
        self.router.add_api_route("/{id}/flat", self.get_one_flat,
                                  methods=['GET'], response_model=self.read_schema,
                                  openapi_extra={'request_model': None})
        self.router.add_api_route("/{id}/api", self.get_one_api, methods=['GET'],
                                  response_model=self.read_api_schema,
                                  openapi_extra={'request_model': None})

    def get_drink_food_service(session: AsyncSession) -> DrinkFoodService:
        repo = DrinkFoodRepository(session)
        return DrinkFoodService(repo)

    async def update_drink_foods(self, id: int,
                                 data: DrinkFoodLinkUpdate,
                                 session: AsyncSession = Depends(get_db)):
        """ обновление many to many """
        service = self.get_drink_food_service(session)
        await service.set_drink_foods(id, data.food_ids)
        return {"status": "success"}

    async def create(self, data: DrinkCreate, session: AsyncSession = Depends(get_db)) -> DrinkCreateResponseSchema:
        """
        Создание одной записи
        """
        try:
            obj, created = await self.service.create(data, self.repo, self.model, session)
            # result = await super().create(data, session)
            return obj
        except ValidationError as exc:
            ValidationError_handler(exc)
            detail = (f'ошибка создания записи {exc}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo} ,'
                      f'create_response_schema = {self.create_response_schema}'
                      )
            print(detail)
        except Exception as e:
            await session.rollback()
            detail = (f'ошибка создания записи {e}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo}')
            print(detail)
            raise HTTPException(status_code=500, detail=detail)

    async def create_relation(self, data: DrinkCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> DrinkRead:
        result = await super().create_relation(data, session)
        return result

    async def patch(self, id: int, data: DrinkUpdate,
                    session: AsyncSession = Depends(get_db)) -> DrinkRead:
        return await super().patch(id, data, session)

    async def create_relation_image(self,
                                    data: str = Form(..., description="JSON string of DrinkCreateRelation"),
                                    file: UploadFile = File(...),
                                    session: AsyncSession = Depends(get_db),
                                    image_service: ImageService = Depends()
                                    ) -> DrinkCreateResponseSchema:
        """
        Создание одной записи с зависимостями - если в таблице есть зависимости
        они будут рекурсивно найдены в связанных таблицах (или добавлены при отсутсвии),
        кроме того будет добавлено изображение
        """
        try:
            data_dict = json.loads(data)
            drink_data = DrinkCreateRelation(**data_dict)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        # content = await file.read()
        image_id, image_path = await image_service.upload_image(file, description=drink_data.title)
        drink_data.image_path = image_path
        result = await super().create_relation(drink_data, session)
        return result

    async def get_one_flat(self, id: int, session: AsyncSession = Depends(get_db)) -> DrinkRead:
        """
            Получение одной записи по ID
        """
        obj = await self.service.get_by_id(id, self.repo, self.model, session)
        # obj = await self.service.get_dict_by_id(id, self.repo, self.model, session)
        return obj  # self.read_schema.model_validate(obj)

    async def get_one_api(self, id: int, session: AsyncSession = Depends(get_db)) -> DrinkReadApi:
        """
            Получение одной записи по ID
        """
        obj = await self.service.get_by_id(id, self.repo, self.model, session)
        return obj  # self.read_schema.model_validate(obj)
