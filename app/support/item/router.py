# app/support/item/router.py
import json
from typing import Optional

from fastapi import Depends, File, Form, HTTPException, Path, Query, status, UploadFile
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.config.project_config import get_paging
from app.core.routers.base import BaseRouter
from app.core.schemas.base import PaginatedResponse
from app.mongodb.service import ThumbnailImageService
from app.support.item.model import Item
from app.support.item.repository import ItemRepository
from app.support.item.schemas import (FileUpload, ItemCreate, ItemCreatePreact, ItemCreateRelation,
                                      ItemCreateResponseSchema, ItemRead, ItemUpdate, ItemUpdatePreact)

paging = get_paging


class ItemRouter(BaseRouter):
    def __init__(self, prefix: str = '/items', **kwargs):
        super().__init__(
            model=Item,
            prefix=prefix,
            repo=ItemRepository
        )
        self.image_service: ThumbnailImageService = Depends()

    def setup_routes(self):
        super().setup_routes()
        # Добавляем маршруты для ListView и DetailView

        self.router.add_api_route(
            "/full", self.create_relation_image, status_code=status.HTTP_200_OK, methods=["POST"],
            # response_model=self.read_schema
            openapi_extra={'request_model': None}
        )
        self.router.add_api_route(
            "/create_item_drink", self.create_item_drink, status_code=status.HTTP_200_OK, methods=["POST"],
            # response_model=ItemCreateResponseSchema
            openapi_extra={'request_model': None}
        )
        # ???????? UPDATE -> POST ?
        self.router.add_api_route(
            "/update_item_drink/{id}", self.update_item_drink, status_code=status.HTTP_200_OK, methods=["POST"],
            # response_model=ItemCreateResponseSchema
            openapi_extra={'request_model': None}
        )
        """ import from upload directory """
        self.router.add_api_route(
            "/direct", self.direct_import_data, status_code=status.HTTP_200_OK, methods=["POST"],
            response_model=dict,
            openapi_extra={'request_model': None})
        self.router.add_api_route(
            "/direct/{id}", self.direct_import_single_data, status_code=status.HTTP_200_OK, methods=["GET"],
            response_model=dict,
            openapi_extra={'request_model': None}
        )

    async def get_list_view(self, lang: str = Path(..., description="Язык локализации"),
                            session: AsyncSession = Depends(get_db)):
        """Получить список элементов с локализацией"""

        items = await self.service.get_list_view(lang, ItemRepository, Item, session)
        return items

    async def get_list_view_paginated(self,
                                      lang: str = Path(..., description="Язык локализации"),
                                      page: int = Query(1, ge=1, description="Номер страницы"),
                                      page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
                                      session: AsyncSession = Depends(get_db)):
        """Получить список элементов с пагинацией и локализацией"""

        result = await self.service.get_list_view_page(page, page_size, ItemRepository, Item, session)
        return result

    async def get_detail_view(self, lang: str = Path(..., description="Язык локализации"),
                              id: int = Path(..., description="ID элемента"),
                              session: AsyncSession = Depends(get_db)):
        """Получить детальную информацию по элементу с локализацией"""

        item = await self.service.get_detail_view(lang, id, ItemRepository, Item, session)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item with id {id} not found")
        return item

    async def create(self, data: ItemCreate,
                     session: AsyncSession = Depends(get_db)) -> ItemCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: ItemUpdate,
                    session: AsyncSession = Depends(get_db)) -> ItemCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: ItemCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> ItemCreateResponseSchema:
        result = await super().create_relation(data, session)
        return result

    async def direct_import_data(self, data: FileUpload,
                                 session: AsyncSession = Depends(get_db),
                                 image_service: ThumbnailImageService = Depends()) -> dict:   # DirectUploadSchema:
        """
        Импорт записей с зависимостями. Для того что бы выполнить импорт нужно
        на сервере поместить файл data.json в директорию UPLOAD_DIR,
        в ту же директорию разместить файлы с изображениями.
        - если в таблице есть зависимости они будут рекурсивно найдены в связанных таблицах (или добавлены при
        отсутсвии), кроме того будет добавлено изображение по его имени
        операция длительная - наберитесь терпения
        """
        # добавление изображений  images={'number of images': 150, 'loaded images': 149}
        _ = await image_service.direct_upload_image()
        # имя json файла для импорта
        file_name = data.filename
        result = await self.service.direct_upload(file_name, session, image_service)
        return result

    async def create_relation_image(self,
                                    data: str = Form(..., description="JSON string of DrinkCreateRelation"),
                                    file: UploadFile = File(...),
                                    session: AsyncSession = Depends(get_db),
                                    image_service: ThumbnailImageService = Depends()
                                    ) -> ItemCreateResponseSchema:
        """
        Создание одной записи с зависимостями - если в таблице есть зависимости
        они будут рекурсивно найдены в связанных таблицах (или добавлены при отсутсвии),
        кроме того будет добавлено изображение.
        перед этим нужно импортировать изображения
        POST mongodb/images/direct
        """
        try:
            data_dict = json.loads(data)
            item_data = ItemCreateRelation(**data_dict)
            # load image to database, get image_id & image_path
            image_dict = await image_service.upload_image(file, description=item_data.drink.title)
            item_data.image_path = image_dict.get('filename')
            item_data.image_id = image_dict.get('id')
            result = await super().create_relation(item_data, session)
            return result
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
        except ValidationError as exc:
            """
            ValidationError_handler(exc)
            detail = (f'ошибка создания записи {exc}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo} ,'
                      f'create_response_schema = {self.create_response_schema}')
            print(detail)
            """
            raise HTTPException(status_code=501, detail=exc)
        except Exception as e:
            await session.rollback()
            detail = (f'ошибка создания записи {e}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo}')
            print(detail)
            raise HTTPException(status_code=500, detail=detail)

    async def create_item_drink(self,
                                data: str = Form(..., description="JSON string of ItemCreatePreact"),
                                file: UploadFile = File(None),
                                session: AsyncSession = Depends(get_db),
                                image_service: ThumbnailImageService = Depends()
                                ) -> ItemCreateResponseSchema:
        """
        Создание записи Item & Drink и всеми связями
        Принимает JSON строку и файл изображения
        Валидирует схемой ItemCreatePreact
        Сохраняет в порядке: Drink -> DrinkVarietal -> DrinkFood -> Item
        """
        try:
            data_dict = json.loads(data)
            item_drink_data = ItemCreatePreact(**data_dict)
            # load image to database, get image_id & image_path
            if file:
                image_dict = await image_service.upload_image(file, description=item_drink_data.title)
                item_drink_data.image_path = image_dict.get('filename')
                item_drink_data.image_id = image_dict.get('id')
            result, _ = await self.service.create_item_drink(item_drink_data, ItemRepository, Item, session)
            return result
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
        except ValidationError as exc:
            # ValidationError_handler(exc)
            detail = (f'ошибка создания записи {exc}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo} ,'
                      f'create_response_schema = {self.create_response_schema}, '
                      f'{data=}')
            print(detail)
            raise HTTPException(status_code=501, detail=exc)
        except Exception as e:
            await session.rollback()
            detail = f'{str(e)}, {data=}'
            print(f'=========={data}')
            raise HTTPException(status_code=500, detail=detail)

    async def update_item_drink(self,
                                id: int,
                                data: str = Form(..., description="JSON string of ItemUpdatePreact"),
                                file: UploadFile = File(None),
                                session: AsyncSession = Depends(get_db),
                                image_service: ThumbnailImageService = Depends()
                                ) -> ItemRead:  # ItemCreateResponseSchema:
        """
        Обновление записи Item & Drink и всеми связями
        Принимает JSON строку и файл изображения
        Валидирует схемой ItemUpdatePreact
        Обновляет или создает Drink в зависимости от drink_action
        """
        try:
            data_dict = json.loads(data)
            drink_action = data_dict.get('drink_action')
            item_drink_data = ItemUpdatePreact(**data_dict)
            # load image to database, get image_id & image_path
            isfile: bool = False
            if file:
                image_dict = await image_service.upload_image(file, description=item_drink_data.title)
                item_drink_data.image_path = image_dict.get('filename')
                item_drink_data.image_id = image_dict.get('id')
                isfile = True
            # item_drink_data.drink_action = drink_action
            # Find the existing item to update
            result = await self.service.update_item_drink(id, item_drink_data, isfile,
                                                          ItemRepository, Item, session)
            if not result.get('success'):
                print(result, 'ошибка обновления')
                raise HTTPException(status_code=500, detail=result.get('message', 'ошибка обновления'))
            return result.get('data')
        except json.JSONDecodeError as e:
            if file and image_dict:
                image_id = image_dict.get('id')
                await image_service.delete_image(image_id)
            raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
        except ValidationError as exc:
            # ValidationError_handler(exc)
            if file and image_dict:
                image_id = image_dict.get('id')
                await image_service.delete_image(image_id)
            detail = (f'ошибка обновления записи {exc}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo} ,'
                      f'create_response_schema = {self.create_response_schema}, '
                      f'{data=}')
            print(detail)
            raise HTTPException(status_code=501, detail=exc)
        except Exception as e:
            if file and image_dict:
                image_id = image_dict.get('id')
                await image_service.delete_image(image_id)
            await session.rollback()
            detail = f'{str(e)}, {data=}'
            print('3rd error', detail)
            raise HTTPException(status_code=500, detail=detail)

    async def direct_import_single_data(self, id: str = Path(..., description="ID элемента"),
                                        session: AsyncSession = Depends(get_db),
                                        image_service: ThumbnailImageService = Depends()) -> dict:
        """
        Импорт записей с зависимостями. Для того что бы выполнить импорт нужно
        на сервере поместить файл data.json в директорию UPLOAD_DIR, в ту же директорию разместить файлы с
        изображениями.
        - если в таблице есть зависимости они будут рекурсивно найдены в связанных таблицах (или добавлены при
        отсутсвии), кроме того будет добавлено изображение по его имени (перед этим выполнить импорт изображений
        /mongodb/images/direct.
        операция длительная - наберитесь терпения
        """
        try:
            id = id.strop('.png')
            result = await self.service.direct_single_upload(id, session)
            # if result.get('error_nmbr', 0) > 0:
            #     raise HTTPException(status_code=423, detail=result)
            return result
        except Exception as e:
            raise HTTPException(status_code=422, detail=e)

    async def search(self,
                     search: Optional[str] = None,
                     country_enum: Optional[str] = None,
                     category_enum: Optional[str] = None,
                     page: int = Query(1, ge=1),
                     page_size: int = Query(paging.get('def', 20),
                                            ge=paging.get('min', 1),
                                            le=paging.get('max', 1000)),
                     session: AsyncSession = Depends(get_db)) -> PaginatedResponse:
        """
            Поиск по всем текстовым полям основной таблицы
            с постраничным выводом результата
        """
        kwargs: str = {'page': page, 'page_size': page_size}
        if search:
            kwargs['search_str'] = search
        if country_enum:
            kwargs['country_enum'] = country_enum
        if category_enum:
            kwargs['category_enum'] = category_enum
        return await self.service.search(self.repo, self.model, session,
                                         **kwargs)

    async def search_all(self,
                         search: Optional[str] = None,
                         country_enum: Optional[str] = None,
                         category_enum: Optional[str] = None,
                         session: AsyncSession = Depends(get_db)) -> PaginatedResponse:
        """
            Поиск по всем текстовым полям основной таблицы
            с постраничным выводом результата
        """
        kwargs: str = {}
        if search:
            kwargs['search_str'] = search
        if country_enum:
            kwargs['country_enum'] = country_enum
        if category_enum:
            kwargs['category_enum'] = category_enum
        return await self.service.search(self.repo, self.model, session,
                                         **kwargs)
