# app/support/item/router_item_view.py
"""
    роутер для ListView и DetailView для модели Item
    выводит плоские словари с локализованными полями
    по языкам
"""
from typing import List, Annotated, Callable
from fastapi import Depends, Path, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db
from app.core.schemas.base import PaginatedResponse
from app.depends import get_translator_func
from app.support.item.model import Item
from app.support.item.repository import ItemRepository
from app.support.item.schemas import ItemDetailView, ItemListView, ItemReadPreactForUpdate, ItemReadRelation
from app.support.item.service import ItemService
from app.core.services.search_service import search_service


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
        """Настройка маршрутов для ListView и DetailView"""
        # Маршрут для получения списка элементов без пагинации
        self.router.add_api_route(
            "/list/{lang}",
            self.get_list,
            methods=["GET"],
            response_model=List[ItemListView],
            tags=self.tags,
            summary="Получить список элементов с локализацией",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для получения списка элементов с пагинацией
        self.router.add_api_route(
            "/list_paginated/{lang}",
            self.get_list_paginated,
            methods=["GET"],
            response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Получить список элементов с пагинацией и локализацией",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для получения одного элемента по id с локализацией
        self.router.add_api_route(
            "/detail/{lang}/{id}",
            self.get_detail,
            methods=["GET"],
            response_model=ItemDetailView,
            tags=self.tags,
            summary="Получить детальную информацию по элементу с локализацией",
            openapi_extra={'x-request-schema': None}
        )

        # 2 Маршрут для поиска элементов по полям title* и subtitle* связанной модели Drink
        self.router.add_api_route(
            "/search_by_drink/{lang}",
            self.search_by_drink_title_subtitle_paginated,
            methods=["GET"],
            response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Поиск элементов по полям title* и subtitle* связанной модели Drink",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для поиска элементов с использованием триграммного индекса
        self.router.add_api_route(
            "/search_trigram/{lang}",
            self.search_by_trigram_index,
            methods=["GET"],
            response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Поиск элементов по триграммному индексу в связанной модели Drink",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для поиска элементов с использованием Meilisearch с пагинацией
        self.router.add_api_route(
            "/search_meilisearch/{lang}",
            self.search_meilisearch_paginated,
            methods=["GET"],
            response_model=PaginatedResponse[ItemReadRelation],
            tags=self.tags,
            summary="Поиск элементов с использованием Meilisearch",
            openapi_extra={'x-request-schema': None}
        )

        # Маршрут для поиска элементов с использованием Meilisearch без пагинации
        self.router.add_api_route(
            "/search_meilisearch_no_pagination/{lang}",
            self.search_meilisearch_no_pagination,
            methods=["GET"],
            response_model=List[ItemReadRelation],
            tags=self.tags,
            summary="Поиск элементов с использованием Meilisearch без пагинации",
            openapi_extra={'x-request-schema': None}
        )

        self.router.add_api_route(
            "/preact/{id}",
            self.get_one,
            methods=["GET"],
            response_model=ItemReadPreactForUpdate,
            tags=self.tags,
            summary="Получить детальную информацию по элементу со всеми локализациями",
            openapi_extra={'x-request-schema': None}
        )

    async def get_one(self,
                      id: int,
                      translation: Annotated[Callable, Depends(get_translator_func)],
                      session: AsyncSession = Depends(get_db)
                      ) -> ItemReadPreactForUpdate:
        """
            Получение одной записи по ID
            используется для загрузки данных в preact for update
            сюда вставляетсяя перевод
        """
        # repo = ItemRepository
        item_dict = await self.service.get_one(id, session)
        # item_py = ItemReadPreactForUpdate.validate(item_dict)
        # item_dict = item_py.model_dump(exclude_unset=False, exclude_none=False)
        translated_dict = await translation(item_dict)
        return translated_dict

    async def get_list(self, lang: str = Path(..., description="Язык локализации"),
                       session: AsyncSession = Depends(get_db)):
        """Получить список элементов с локализацией"""
        result = await self.service.get_list_view(lang, ItemRepository, Item, session)

        return result

    async def get_list_paginated(self,
                                 lang: str = Path(..., description="Язык локализации"),
                                 page: int = Query(1, ge=1, description="Номер страницы"),
                                 page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
                                 session: AsyncSession = Depends(get_db)):
        """Получить список элементов с пагинацией и локализацией"""
        result = await self.service.get_list_view_page(page, page_size, ItemRepository, Item, session, lang)
        # self.paginated_response

        return result

    async def get_detail(self, lang: str = Path(..., description="Язык локализации"),
                         id: int = Path(..., description="ID элемента"),
                         session: AsyncSession = Depends(get_db)):
        """Получить детальную информацию по элементу с локализацией"""
        item = await self.service.get_detail_view(lang, id, ItemRepository, Item, session)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item with id {id} not found")
        # Create ItemDetailView instance
        result = ItemDetailView(**item)

        # Return the model dump with empty values removed
        return result.model_dump(exclude_none=True, exclude_unset=True)

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
        return result

    async def search_by_trigram_index(self,
                                      lang: str = Path(..., description="Язык локализации"),
                                      search_str: str = Query(
                                          None, description="Поисковый запрос "
                                                            "(при отсутствии значения - выдает все записи)"),
                                      page: int = Query(1, ge=1, description="Номер страницы"),
                                      page_size: int = Query(15, ge=1, le=100, description="Размер страницы"),
                                      session: AsyncSession = Depends(get_db)):
        """Поиск элементов с использованием триграммного индекса в связанной модели Drink"""
        result = await self.service.search_by_trigram_index(
            search_str, lang, ItemRepository, Item, session, page, page_size
        )

        return result

    async def search_meilisearch_paginated(self,
                                           lang: str = Path(..., description="Язык локализации"),
                                           query: str = Query(..., description="Поисковый запрос для Meilisearch"),
                                           page: int = Query(1, ge=1, description="Номер страницы"),
                                           page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
                                           session: AsyncSession = Depends(get_db)
                                           ):
        """Поиск элементов с использованием Meilisearch с пагинацией"""
        try:
            search_result = await search_service.search(query, page, page_size, lang)

            # Convert the search results to ItemReadRelation models
            items = []
            for hit in search_result['results']:
                # Validate and convert each result to ItemReadRelation
                item_data = ItemReadRelation.model_validate(hit)
                items.append(item_data)

            # Create paginated response
            total = search_result.get('total', len(items))
            total_pages = search_result.get('total_pages', 1)

            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    async def search_meilisearch_no_pagination(self,
                                               lang: str = Path(..., description="Язык локализации"),
                                               query: str = Query(..., description="Поисковый запрос для Meilisearch"),
                                               session: AsyncSession = Depends(get_db)):
        """Поиск элементов с использованием Meilisearch без пагинации"""
        try:
            # Perform search with a large page size to get all results
            search_result = await search_service.search(query, page=1, page_size=1000, lang=lang)

            # Convert the search results to ItemReadRelation models
            items = []
            for hit in search_result['results']:
                # Validate and convert each result to ItemReadRelation
                item_data = ItemReadRelation.model_validate(hit)
                items.append(item_data)

            return items
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
