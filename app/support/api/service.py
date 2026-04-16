# app.support.api.service.py
from pydantic import TypeAdapter
from decimal import Decimal
from fastapi import HTTPException
from typing import List, Dict, Any, Type
from datetime import datetime
from loguru import logger
# from sqlalchemy.sql.elements import Label
# from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.utils.pydantic_utils import get_field_name, make_paginated_response, inst_dict, list_dict
from app.core.utils.common_utils import camel_to_enum
from app.support.item.service import ItemService
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.item.repository import ItemRepository
from app.support.item.model import Item
from app.core.utils.common_utils import localized_field_with_replacement
from app.core.utils.converters import lang_suffix_list, lang_suffix_dict
from app.core.utils.alchemy_utils import formatted_query, transform_api_list_view
from app.core.config.project_config import settings
from app.core.schemas.base import PaginatedResponse
from app.support.item.schemas import (ItemApiLangNonLocalized, ItemApi,
                                      ItemApiLangLocalizedInterim)

ItemApiAdapter: TypeAdapter = TypeAdapter(List[ItemApi])
language: list = settings.LANGUAGES
# список языковых суффиксов
lang_prefixes: list = lang_suffix_list(language)
def_lang = settings.DEFAULT_LANG
# словарь {'en': ['', '_ru': '_fr'],...}
# списки языков отсортированы в порядке очередности замены для каждого языка
lang_dict = lang_suffix_dict(language)
itemapilangnonlocalized = get_field_name(ItemApiLangNonLocalized)
itemapilanglocalized = get_field_name(ItemApiLangLocalizedInterim)


class ApiService(ItemService):

    @classmethod
    def __api_view__(cls, item: dict) -> dict:
        """
            логика метода get_api_view
        """
        try:
            # задаем порядок замещения пустых полей
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
                    if key == 'category':
                        if val.get('name') in ('Wine', 'wine'):
                            val = item.get('subcategory')
                        if val.get('name') in ('Other', 'other'):
                            item['type'] = item.get('subcategory')
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
                for k in itemapilangnonlocalized:
                    v = item.get(k)
                    if isinstance(v, (float, Decimal)):
                        v = f"{v:.03g}"
                    dict_lang[k] = v
                # add localized subfields to localized fields
                for k in itemapilanglocalized:
                    if k == 'site':  # вложенные сущности
                        site = item.get('site')
                        subregion = site.get('subregion')
                        region = subregion.get('region')
                        lf = localized_field_with_replacement(region, 'name', lang_suff, 'region')
                        lt = localized_field_with_replacement(subregion, 'name', lang_suff, 'subregion')
                        lf['region'] = f"{lf['region']}. {lt['subregion']}".replace('None', '').replace('..', '.').strip()
                    elif k == 'type':  # subcategory for other
                        if subcategory := item.get('subcategory'):
                            if ((category := subcategory.get('category')) and
                                    (cat_name := category.get('name'))) and (cat_name in ('Wine', 'wine')):
                                continue
                            lf = localized_field_with_replacement(subcategory, 'name', lang_suff, k)
                    else:
                        lf = localized_field_with_replacement(item, k, lang_suff)
                    if lf:
                        dict_lang.update(lf)
                # add many-to-many fields
                many_to_many = cls.add_manytomany_fields(item, lang_suff)
                dict_lang.update(many_to_many)
                result[key] = dict_lang
                # validated_result = ItemApiLang.model_validate(dict_lang)
                # result[key] = validated_result.model_dump(exclude_none=True, exclude_unset=True)
            return result
        except Exception as e:
            print(f'__api_view__.error {e} {item.get("id")=}')
            raise HTTPException(status_code=503, detail=f'error.__api_view__.{e}')

    @classmethod
    def convert_list_api_view(cls, items: List[ModelType]) -> List[Dict[str, Any]]:
        # api_view = cls.__api_view__
        api_view = transform_api_list_view
        cleaned_list = [api_view(inst_dict(item), def_lang, lang_prefixes) for item in items]
        # result = ItemApiAdapter.validate_python([api_view(item.to_dict()) for item in items])
        # cleaned_list = [item.model_dump(exclude_none=True, exclude_defaults=True) for item in result]
        return cleaned_list

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
        item_instance = await repository.get_detail_view(id, Item, session)
        if not item_instance:
            return None
        item: dict = inst_dict(item_instance)
        # result: dict = cls.__api_view__(item)
        result: dict = transform_api_list_view(item, def_lang, lang_prefixes)
        return result

    @classmethod
    async def get_list_api_view(cls, after_date: datetime, repository, model,
                                session: AsyncSession,):
        """ Получение списка элементов для api view """
        items = await repository.get_all(after_date, model, session)
        result = cls.convert_list_api_view(items)
        return result

    @classmethod
    async def get_list_api_view_page(cls, ater_date: datetime, page: int, page_size: int,
                                     repository: ItemRepository, model: Item, session: AsyncSession):
        """Получение списка элементов для ListView с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.get(ater_date, skip, page_size, model, session)
        result = cls.convert_list_api_view(items)
        # result = []
        # for item in items:
        #     if item_dict := item.to_dict():
        #         result.append(cls.__api_view__(item_dict))
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def search(cls, search: str, page: int, page_size: int,
                     repository: ItemRepository, model: Item,
                     session: AsyncSession
                     ) -> PaginatedResponse[ItemApi]:
        """Поиск с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.search(search, skip, page_size, model, session)
        result = cls.convert_list_api_view(items)
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def search_all(cls, search: str,
                         repository: ItemRepository, model: Item,
                         session: AsyncSession, limit: int = 20) -> PaginatedResponse[ItemApi]:
        """Поиск с пагинацией и локализацией"""
        items = await repository.search_all(search, model, session)
        result = cls.convert_list_api_view(items)
        return result

    @classmethod
    async def search_geans(cls, search: str, similarity_threshold: float,
                           page: int, page_size: int,
                           repository: ItemRepository, model: Item, session: AsyncSession) -> Dict[str, Any]:
        """ DEPRECATED """
        try:
            response = await super().search_geans(search,
                                                  similarity_threshold, page, page_size, repository, model,
                                                  session)
            items: dict = response.get('items')
            if not items:
                raise HTTPException(status_code=404, details=f'found nothig by request "{search}"')
            response['itmes'] = cls.convert_list_api_view(items)
            return response
            skip = (page - 1) * page_size
            if not search:
                items, total = await repository.get_full_with_pagination(skip, page_size, model, session)
            else:
                # relevance: Label = await cls.get_relevance(search, model, session, similarity_threshold)
                if formatted_search := formatted_query(search):
                    items, total = await repository.search_fts(formatted_search, skip, page_size, model, session)
                else:
                    items, total = await repository.search_by_drink_title_subtitle(search, session, skip, page_size)
            items = list_dict(items)
            result = cls.convert_list_api_view(items)
            return make_paginated_response(result, total, page, page_size)
        except Exception as e:
            logger.error(f'search_geans. {e}')
            raise HTTPException(status_code=502, detail=f'search_geans. {e}')

    @classmethod
    async def search_geans_all(cls, search: str,
                               repository: Type[ItemRepository],
                               model: ModelType, session: AsyncSession,
                               limit: int = 20) -> List[dict]:
        """ DEPRECATED переделан под полнотекстовый поиск """
        try:
            logger.warning('geans type of search is deprecated. redirect to fts (if available ) or '
                           'drink_title_subtitle')
            if not search:
                items = await repository.get_full(model, session)
            else:
                if formatted_search := formatted_query(search):
                    items = await repository.search_fts_all(formatted_search, model, session)
                else:
                    items = await repository.search_by_drink_title_subtitle_only(search, session)
            result = cls.convert_list_api_view(items)
            return result
        except Exception as e:
            logger.error(f'search_gens_all. {e}')
            raise HTTPException(status_code=503, detail=f'search_gens_all. {e}')

    @classmethod
    async def get_list_api_view_ids(cls, ids: str, repository, model,
                                    session: AsyncSession,):
        """ Получение списка элементов для api view """
        if not ids:
            return []
        comma_separator = ','
        ids_set = tuple(int(b) for a in set(ids.split(comma_separator)) if (b := a.strip()).isdigit())
        items = await repository.get_by_ids(ids_set, model, session)
        result = cls.convert_list_api_view(items)
        return result

    @classmethod
    async def execute_smart_search(cls, query: str, session: AsyncSession, boost: float = 15.0, limit: int = 20):
        items = await super().execute_smart_search(query, session, boost, limit)
        return [transform_api_list_view(item, def_lang, lang_prefixes) for item in items]
