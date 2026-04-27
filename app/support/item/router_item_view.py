# app/support/item/router_item_view.py
"""
    роутер для ListView и DetailView для модели Item
    выводит плоские словари с локализованными полями
    по языкам
"""
from typing import List, Annotated, Callable
from fastapi import Depends, Path, Query, HTTPException, BackgroundTasks, Form, UploadFile, File
import json
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db, DatabaseManager
from app.core.utils.pydantic_utils import orresponse
from app.core.schemas.base import PaginatedResponse
from app.dependencies import get_translator_func
from app.mongodb.service import ThumbnailImageService
from app.support.item.model import Item
from app.support.item.repository import ItemRepository
from app.support.item.schemas import ItemListView, ItemUpdatePreact
from app.support.item.service import ItemService


class ItemViewRouter:
    def __init__(self, prefix: str = '/items_view', tags: List[str] = None):
        from fastapi import APIRouter
        self.prefix = prefix
        self.tags = tags or ["items_view"]
        # self.router = APIRouter()
        self.router = APIRouter(dependencies=[Depends(get_active_user_or_internal)])
        self.service = ItemService()
        self.paginated_response = PaginatedResponse[ItemListView]
        self.setup_routes()

    def setup_routes(self):
        """
        self.router.add_api_route(
            "/create",
            self.create_item,
            methods=['POST'],
            response_model=ItemCreateResponseSchema,
            tags=self.tags,
            summary="Создание напитка в упаковке с этикеткой"
        )
        """
        self.router.add_api_route(
                "/update_item_drink/{id}", self.update_item_drink, methods = ["PATH"], tags = self.tags,
                summary = "Поиск элементов по hash index + word..", # response_model=ItemCreateResponseSchema,
                openapi_extra = {'x-request-schema': None}
                )
        """Настройка маршрутов для ListView и DetailView"""
        # Маршрут для получения списка элементов без пагинации
        self.router.add_api_route(
            "/list/{lang}",
            self.get_list,
            methods=["GET"],
            # response_model=List[ItemListView],
            tags=self.tags,
            summary="Получить список элементов с локализацией",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для получения списка элементов с пагинацией
        self.router.add_api_route(
            "/list_paginated/{lang}",
            self.get_list_paginated,
            methods=["GET"],
            # response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Получить список элементов с пагинацией и локализацией",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для получения одного элемента по id с локализацией
        self.router.add_api_route(
            "/detail/{lang}/{id}",
            self.get_detail,
            methods=["GET"],
            # response_model=ItemDetailView,
            tags=self.tags,
            summary="Получить детальную информацию по элементу с локализацией",
            openapi_extra={'x-request-schema': None}
        )

        # 2 Маршрут для поиска элементов по полям title* и subtitle* связанной модели Drink
        self.router.add_api_route(
            "/search_by_drink/{lang}",
            self.search_by_drink_title_subtitle_paginated,
            methods=["GET"],
            # response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Поиск элементов по полям title* и subtitle* связанной модели Drink",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для поиска элементов с использованием fts индекса
        self.router.add_api_route(
            "/search_trigram/{lang}",  # путь не менять - используется preact
            self.search_by_geans_items,
            methods=["GET"],
            # response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Поиск элементов по fts index",
            openapi_extra={'x-request-schema': None}
        )
        # Маршрут для поиска элементов с использованием fts индекса
        self.router.add_api_route(
            "/search_smart",
            self.search_smart,
            methods=["GET"],
            # response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Поиск элементов по hash index + word..",
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/preact/{id}",
            self.get_one,
            methods=["GET"],
            # response_model=ItemReadPreactForUpdate,
            tags=self.tags,
            summary="Получить детальную информацию по элементу со всеми локализациями",
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/fill_index",
            self.fill_index, methods=["GET"],
            tags=self.tags, summary="заполнить полнотекстовый индекс",
            openapi_extra={'x-request-schema': None}
        )

    async def get_one(self,
                      id: int,
                      translation: Annotated[Callable, Depends(get_translator_func)],
                      session: AsyncSession = Depends(get_db)
                      ):
        """
            Получение одной записи по ID
            используется для загрузки данных в preact for update
            сюда вставляетсяя перевод
        """
        # repo = ItemRepository
        item_dict = await self.service.get_one(id, session)
        # item_py = ItemReadPreactForUpdate.validate(item_dict)
        # item_dict = item_py.model_dump(exclude_unset=False, exclude_none=False)
        translated_dict = item_dict  # await translation(item_dict)
        return translated_dict

    async def get_list(self, lang: str = Path(..., description="Язык локализации"),
                       session: AsyncSession = Depends(get_db),
                       limit: int = 20):
        """Получить список элементов с локализацией"""

        result = await self.service.get_list_view(lang, ItemRepository, Item, session, limit)
        return orresponse(result)
        # return result

    async def get_list_paginated(self,
                                 lang: str = Path(..., description="Язык локализации"),
                                 page: int = Query(1, ge=1, description="Номер страницы"),
                                 page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
                                 session: AsyncSession = Depends(get_db)):
        """Получить список элементов с пагинацией и локализацией"""
        result = await self.service.get_list_view_page(page, page_size, ItemRepository, Item, session, lang)
        return orresponse(result)

    async def get_detail(self, lang: str = Path(..., description="Язык локализации"),
                         id: int = Path(..., description="ID элемента"),
                         session: AsyncSession = Depends(get_db)):
        """Получить детальную информацию по элементу с локализацией"""
        item = await self.service.get_detail_view(lang, id, ItemRepository, Item, session)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item with id {id} not found")
        # Create ItemDetailView instance
        # result = ItemDetailView.validate(item)
        return item

    async def search_by_drink_title_subtitle_paginated(self,
                                                       lang: str = Path(..., description="Язык локализации"),
                                                       search: str = Query(
                                                           ..., description="Строка для поиска в полях title* "
                                                                            "и subtitle* модели Drink"),
                                                       page: int = Query(1, ge=1, description="Номер страницы"),
                                                       page_size: int = Query(
                                                           20, ge=1, le=100, description="Размер страницы"),
                                                       session: AsyncSession = Depends(get_db)):
        """
            Поиск элементов по полям title* и subtitle* связанной модели Drink с пагинацией
            оатсется для совместимости (сравнить скорость поиска обычного (этого) и триграмм/FTS
        """
        result = await self.service.search_by_drink_title_subtitle(
            search, lang, ItemRepository, Item, session, page, page_size
        )
        return orresponse(result)

    async def search_by_geans_items(self,
                                    lang: str = Path(..., description="Язык локализации"),
                                    search_str: str = Query(
                                        None, description="Поисковый запрос "
                                        "(при отсутствии значения - выдает все записи)"),
                                    page: int = Query(1, ge=1, description="Номер страницы"),
                                    page_size: int = Query(15, ge=1, le=100, description="Размер страницы"),
                                    similarity_thershold: float = Query(0.2,
                                                                        ge=0., le=1.0,
                                                                        description=("Толерантность поиска")),
                                    session: AsyncSession = Depends(get_db)):
        """ новый поиск вместо триграмного  индекса ONLY FOR ITEMS_PREACT        """
        # result = await self.service.search_by_trigram_index(search_str, lang, ItemRepository,
        #                                                     Item, session, page, page_size)
        result = await self.service.search_geans_items(lang, search_str, similarity_thershold,
                                                       page, page_size, ItemRepository,
                                                       Item, session)
        return result

    async def fill_index(self, background_tasks: BackgroundTasks,
                         session: AsyncSession = Depends(get_db),
                         force_all: bool = False):
        """
             старт заполнения индекса! результат см в логах
        """
        await self.service.run_reindex_worker(DatabaseManager.session_maker, force_all, background_tasks=background_tasks)
        # await self.service.run_background_task(background_tasks, session, force_all)
        return {'result': True}

    async def search_smart(self,
                           # lang: str = Path(..., description="Язык локализации"),
                           search_str: str = Query(
                               None, description="Поисковый запрос "
                               "(при отсутствии значения - выдает все записи)"),
                           # page: int = Query(1, ge=1, description="Номер страницы"),
                           # page_size: int = Query(15, ge=1, le=100, description="Размер страницы"),
                           session: AsyncSession = Depends(get_db),
                           boost: float = Query(
                               15.0, description="Премия за редкое слово "
                               "(записи с редким словом из запроса попадают наверх выборки)"),
                           limit: int = Query(15, description='Количество записей (большое чиcло вызовет тормоза)')):
        """ новый поиск вместо триграмного  индекса ONLY FOR ITEMS_PREACT        """
        # result = await self.service.search_by_trigram_index(search_str, lang, ItemRepository,
        #                                                     Item, session, page, page_size)
        result = await self.service.execute_smart_search(search_str, session, boost, limit)
        return orresponse(result)

    async def search_smart_keyset(self,
                                  # lang: str = Path(..., description="Язык локализации"),
                                  search_str: str = Query(
                                      None, description="Поисковый запрос "
                                      "(при отсутствии значения - выдает все записи)"),
                                  page: int = Query(1, ge=1, description="Номер страницы"),
                                  page_size: int = Query(15, ge=1, le=100, description="Размер страницы"),
                                  session: AsyncSession = Depends(get_db)):
        """ новый поиск вместо триграмного  индекса ONLY FOR ITEMS_PREACT        """
        # result = await self.service.search_by_trigram_index(search_str, lang, ItemRepository,
        #                                                     Item, session, page, page_size)

        result = await self.search_smart_keyset(search_str, page, page_size, session)
        return result

    async def update_item_drink(self,
                                id: int,
                                background_tasks: BackgroundTasks,
                                data: str = Form(..., description="JSON string of ItemUpdatePreact"),
                                file: UploadFile = File(None),
                                session: AsyncSession = Depends(get_db),
                                image_service: ThumbnailImageService = Depends()
                                ):  # ItemCreateResponseSchema:
        """
        Обновление записи Item & Drink и всеми связями PREACT
        Принимает JSON строку и файл изображения
        Валидирует схемой ItemUpdatePreact
        Обновляет или создает Drink в зависимости от drink_action
        """
        try:
            data_dict = json.loads(data)
            data_dict['drink_action'] = 'update'
            from app.core.utils.common_utils import jprint
            jprint(data_dict)

            if file:
                image_dict = await image_service.upload_image(file, description=data_dict.get('title'))
                jprint(image_dict)
                data_dict['image_id'] = image_dict.get('id')
                data_dict['image_path'] = image_dict.get('filename')
            item_drink_data = ItemUpdatePreact(**data_dict)
            result = await self.service.update_item_drink(id, item_drink_data,
                                                          ItemRepository, Item, background_tasks,
                                                          session)
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
            raise HTTPException(status_code=501, detail=exc)
        except Exception as e:
            if file and image_dict:
                image_id = image_dict.get('id')
                await image_service.delete_image(image_id)
            detail = f'{str(e)}, {data=}'
            print('3rd error', detail)
            raise HTTPException(status_code=500, detail=detail)
