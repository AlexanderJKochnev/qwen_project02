# app/support/item/router_item_view.py
"""
    роутер для ListView и DetailView для модели Item
    выводит плоские словари с локализованными полями
    по языкам
"""
from typing import List, Annotated, Callable
from fastapi import Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db
from app.core.schemas.base import PaginatedResponse
from app.depends import get_translator_func
from app.support.item.model import Item
from app.support.item.repository import ItemRepository
from app.support.item.schemas import ItemDetailView, ItemListView, ItemReadPreactForUpdate
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
        """Настройка маршрутов для ListView и DetailView"""
        # Маршрут для получения списка элементов без пагинации
        self.router.add_api_route(
            "/list/{lang}",
            self.get_list,
            methods=["GET"],
            response_model=List[ItemListView],
            tags=self.tags,
            summary="Получить список элементов с локализацией"
        )

        # Маршрут для получения списка элементов с пагинацией
        self.router.add_api_route(
            "/list_paginated/{lang}",
            self.get_list_paginated,
            methods=["GET"],
            response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Получить список элементов с пагинацией и локализацией"
        )

        # Маршрут для получения одного элемента по id с локализацией
        self.router.add_api_route(
            "/detail/{lang}/{id}",
            self.get_detail,
            methods=["GET"],
            response_model=ItemDetailView,
            tags=self.tags,
            summary="Получить детальную информацию по элементу с локализацией"
        )

        # 2 Маршрут для поиска элементов по полям title* и subtitle* связанной модели Drink
        self.router.add_api_route(
            "/search_by_drink/{lang}",
            self.search_by_drink_title_subtitle_paginated,
            methods=["GET"],
            response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Поиск элементов по полям title* и subtitle* связанной модели Drink"
        )

        # Маршрут для поиска элементов с использованием триграммного индекса
        self.router.add_api_route(
            "/search_trigram/{lang}",
            self.search_by_trigram_index,
            methods=["GET"],
            response_model=PaginatedResponse[ItemListView],
            tags=self.tags,
            summary="Поиск элементов по триграммному индексу в связанной модели Drink"
        )

        self.router.add_api_route(
            "/preact/{id}",
            self.get_one,
            methods=["GET"],
            response_model=ItemReadPreactForUpdate,
            tags=self.tags,
            summary="Получить детальную информацию по элементу со всеми локализациями"
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
        translated_dict = await translation(item_dict, True)
        for key, val in translated_dict.items():
            print(f'{key}: new {val}, old {item_dict.get(key)}')
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
            from fastapi import HTTPException
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
