# app.support.api.service.py
from decimal import Decimal
from fastapi import HTTPException
from typing import List, Type, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.sql.elements import Label
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.utils.alchemy_utils import ModelType
from app.core.utils.pydantic_utils import get_field_name, make_paginated_response
from app.core.utils.common_utils import camel_to_enum
from app.support.item.service import ItemService
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.item.repository import ItemRepository
from app.support.item.model import Item
from app.core.utils import localized_field_with_replacement
from app.core.utils.converters import lang_suffix_list, lang_suffix_dict
from app.core.config.project_config import settings
from app.core.schemas.base import PaginatedResponse
from app.support.item.schemas import ItemApiLangNonLocalized, ItemApiLangLocalized, ItemApiLang, ItemApi


class ApiService(ItemService):

    @classmethod
    def __api_view__(cls, item: dict) -> dict:
        """ логика метода get_api_view
            что на входе?
        """
        try:
            # задаем порядок замещения пустых полей
            language: list = settings.LANGUAGES
            # список языковых суффиксов
            lang_prefixes: list = lang_suffix_list(language)
            # словарь {'en': ['', '_ru': '_fr'],...}
            # списки языков отсортированы в порядке очередности замены для каждого языка
            lang_dict = lang_suffix_dict(language)
            # перенос вложенных словарей на верхний уровень (drink -> root)
            item = cls._level_up_(lang_prefixes, item)
            item['changed_at'] = item.pop('updated_at')
            result: dict = {}
            # добавление корневых не локализованных полей
            # country enum - только на англ enum
            # category - только на англ enum
            root_fields = settings.api_root_fields
            # add root fields
            for key in root_fields:
                if val := item.get(key):
                    if key == 'category' and val == 'Wine':
                        val = item.get('subcategory')
                    if isinstance(val, (float, Decimal)):
                        val = f"{val:.03g}"
                    elif isinstance(val, dict):
                        val = camel_to_enum(val.get('name'))
                    result[key] = val
        # try:
            # add localized fields:
            for key, lang_suff in lang_dict.items():
                dict_lang = {}
                # add non-localized subfields to localized fields
                for k in get_field_name(ItemApiLangNonLocalized):
                    v = item.get(k)
                    if isinstance(v, (float, Decimal)):
                        v = f"{v:.03g}"
                    dict_lang[k] = v
                # add localized subfields to localized fields
                for k in get_field_name(ItemApiLangLocalized):
                    if k == 'region':  # вложенные сущности
                        subregion = item.get('subregion')
                        region = subregion.get('region')
                        lf = localized_field_with_replacement(region, 'name', lang_suff, k)
                        lt = localized_field_with_replacement(subregion, 'name', lang_suff)
                        lf['region'] = f"{lf['region']}. {lt['name']}".replace('None', '').replace('..', '.')
                    else:
                        lf = localized_field_with_replacement(item, k, lang_suff)
                    if lf:
                        dict_lang.update(lf)

                # add many-to-many fields
                many_to_many = cls.add_manytomany_fields(item, lang_suff)
                dict_lang.update(many_to_many)
                validated_result = ItemApiLang.model_validate(dict_lang)
                result[key] = validated_result.model_dump(exclude_none=True)
            validated_result = ItemApi.model_validate(result)
            return validated_result
        except Exception as e:
            print(f'__api_view__.error {e} {item.get("id")=}')
            raise HTTPException(status_code=503, detail=f'error.__api_view__.{e}')

    @classmethod
    async def get_item_api_view(cls, id: int, session: AsyncSession):
        """
            Получение представления элемента с локализацией by lang
            {
              "image_id": "string",
              "image_path": "string",
              "id": 0,
              "vol": 0,
              "changed_at": "2026-01-16T19:17:33.245Z",
              "country": "string",
              "category": "string",
              "en": {
                "description": "string",
                "title": "string",
                "subtitle": "string",
                "alc": "13.5%",
                "pairing": [
                  "string",
                  "string"
                ],
                "varietal": [
                  "Cabernet Sauvignon 85%",
                  "Cabernet Franc 15%"
                ]
              },
            }
        """
        repository = ItemRepository
        model = Item
        item_instance = await repository.get_detail_view(id, model, session)
        item: dict = item_instance.to_dict()
        if not item:
            return None
        result = cls.__api_view__(item)
        return result

    @classmethod
    async def get_list_api_view(cls, after_date: datetime, repository, model,
                                session: AsyncSession,):
        """ Получение списка элементов для api view """
        items = await repository.get(after_date, model, session)
        result = []
        for item in items:
            item_dict = item.to_dict()
            result.append(cls.__api_view__(item_dict))
        return result

    @classmethod
    async def get_list_api_view_page(cls, ater_date: datetime, page: int, page_size: int,
                                     repository: ItemRepository, model: Item, session: AsyncSession):
        """Получение списка элементов для ListView с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.get_all(ater_date, skip, page_size, model, session)
        result = []
        for item in items:
            if item_dict := item.to_dict():
                result.append(cls.__api_view__(item_dict))
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def search(cls, search: str, page: int, page_size: int,
                     repository: ItemRepository, model: Item,
                     session: AsyncSession
                     ) -> PaginatedResponse[ItemApi]:
        """Поиск с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.search(search, skip, page_size, model, session)
        result = []
        for item in items:
            if item_dict := item.to_dict():
                result.append(cls.__api_view__(item_dict))
        result = make_paginated_response(result, total, page, page_size)
        return result

    @classmethod
    async def search_all(cls, search: str,
                         repository: ItemRepository, model: Item,
                         session: AsyncSession) -> PaginatedResponse[ItemApi]:
        """Поиск с пагинацией и локализацией"""
        items = await repository.search_all(search, model, session)
        result = []
        for item in items:
            if item_dict := item.to_dict():
                result.append(cls.__api_view__(item_dict))
        return result

    @classmethod
    async def search_geans(cls, search: str, similarity_threshold: float,
                           page: int, page_size: int,
                           repository: ItemRepository, model: Item, session: AsyncSession) -> Dict[str, Any]:
        try:
            skip = (page - 1) * page_size
            if not search:
                items, total = await repository.get_full_with_pagination(skip, page_size, model, session)
            else:
                # relevance: Label = await cls.get_relevance(search, model, session, similarity_threshold)
                items, total = await repository.search_fts(search, skip, page_size, model, session)
            result = []
            for item in items:
                if item_dict := item.to_dict():
                    result.append(cls.__api_view__(item_dict))
            return make_paginated_response(result, total, page, page_size)
        except Exception as e:
            logger.error(f'search_geans. {e}')
            raise HTTPException(status_code=502, detail=f'search_geans. {e}')

    @classmethod
    async def search_geans_all(cls, search: str, similarity_threshold: float,
                               repository: Type[Repository],
                               model: ModelType, session: AsyncSession) -> List[dict]:
        """ перделан под полнотекстовый поиск """
        try:
            if not search:
                items = await repository.get_full(model, session)
            else:
                # relevance: Label = await cls.get_relevance(search, model, session, similarity_threshold)
                items = await repository.search_fts_all(search, model, session)
            result = []
            for item in items:
                if item_dict := item.to_dict():
                    x = cls.__api_view__(item_dict)
                    result.append(x)
            return result
        except Exception as e:
            logger.error(f'search_gens_all. {e}')
            raise HTTPException(status_code=503, detail=f'search_gens_all. {e}')
