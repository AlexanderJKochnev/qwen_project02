# app.support.api.service.py
# from pydantic import TypeAdapter
from decimal import Decimal
from fastapi import HTTPException, Request
from typing import List, Dict, Any
from datetime import datetime
# from sqlalchemy.sql.elements import Label
# from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.core.utils.image_utils import get_default_image
# from app.core.repositories.sqlalchemy_repository import Repository
from app.core.utils.pydantic_utils import get_field_name, make_paginated_response, inst_dict, list_dict
from app.core.utils.common_utils import camel_to_enum
from app.support.item.service import ItemService
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.item.repository import ItemRepository
from app.support.item.model import Item
from app.core.utils.common_utils import localized_field_with_replacement
# from app.core.utils.converters import lang_suffix_list, lang_suffix_dict
from app.core.utils.alchemy_utils import formatted_query, transform_api_list_view
from app.core.config.project_config import settings
from app.core.schemas.base import PaginatedResponse
from app.support.item.schemas import (ItemApiLangNonLocalized, ItemApi,
                                      ItemApiLangLocalizedInterim)

# ItemApiAdapter: TypeAdapter = TypeAdapter(List[ItemApi])
language: list = settings.LANGUAGES
# список языковых суффиксов
# lang_prefixes: list = cls.lang_suffix_list(language)
def_lang = settings.DEFAULT_LANG
# словарь {'en': ['', '_ru': '_fr'],...}
# списки языков отсортированы в порядке очередности замены для каждого языка
# lang_dict = lang_suffix_dict(language)
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
            item = cls._level_up_(cls.lang_suffix_list(language), item)
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
            lang_dict = cls.lang_suffix_dict(language)
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
                        lf['region'] = f"{lf['region']}. {lt['subregion']}".replace(
                            'None', '').replace('..', '.').strip()
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
    def convert_list_api_view(cls, request: Request, items: List[ModelType], cnv: bool = True) -> List[Dict[str, Any]]:
        """
            cnv
        """
        api_view = transform_api_list_view
        lang_prefixes = cls.lang_suffix_list(language)
        default_image_id = get_default_image(request, 1)  # заглушка для thumbnails
        if cnv:
            cleaned_list = [api_view(inst_dict(item), def_lang, lang_prefixes, default_image_id) for item in items]
        else:
            cleaned_list = [api_view(item, def_lang, lang_prefixes, default_image_id) for item in items]
        # result = ItemApiAdapter.validate_python([api_view(item.to_dict()) for item in items])
        # cleaned_list = [item.model_dump(exclude_none=True, exclude_defaults=True) for item in result]
        return cleaned_list

    @classmethod
    async def get_item_api_view(cls, request: Request, id: int, session: AsyncSession):
        """
            Получение представления элемента с локализацией by lang
        """
        repository = ItemRepository
        default_image_id = get_default_image(request, 0)
        item_instance = await repository.get_detail_view(id, Item, session)
        if not item_instance:
            return None
        item: dict = inst_dict(item_instance)
        # result: dict = cls.__api_view__(item)
        result: dict = transform_api_list_view(item, def_lang, cls.lang_suffix_list(language), default_image_id)
        return result

    @classmethod
    async def get_list_api_view(cls, request: Request, after_date: datetime, repository, model,
                                session: AsyncSession,):
        """ Получение списка элементов для api view """
        items = await repository.get_all(after_date, model, session)
        result = cls.convert_list_api_view(request, items)
        return result

    @classmethod
    async def get_list_api_view_page(cls, request: Request, ater_date: datetime, page: int, page_size: int,
                                     repository: ItemRepository, model: Item, session: AsyncSession):
        """Получение списка элементов для ListView с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.get(ater_date, skip, page_size, model, session)
        default_image_id = get_default_image(request, 1)  # заглушка для thumbnails
        result = cls.convert_list_api_view(request, items, default_image_id)
        # result = []
        # for item in items:
        #     if item_dict := item.to_dict():
        #         result.append(cls.__api_view__(item_dict))
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def search(cls, request: Request, search: str, page: int, page_size: int,
                     repository: ItemRepository, model: Item,
                     session: AsyncSession
                     ) -> PaginatedResponse[ItemApi]:
        """Поиск с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.search(search, skip, page_size, model, session)
        default_image_id = get_default_image(request, 1)  # заглушка для thumbnails
        result = cls.convert_list_api_view(request, items, default_image_id)
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def search_all(cls, request: Request, search: str,
                         repository: ItemRepository, model: Item,
                         session: AsyncSession, limit: int = 20) -> PaginatedResponse[ItemApi]:
        """Поиск с пагинацией и локализацией"""
        items = await repository.search_all(search, model, session)
        default_image_id = get_default_image(request, 1)  # заглушка для thumbnails
        result = cls.convert_list_api_view(request, items, default_image_id)
        return result

    @classmethod
    async def get_list_api_view_ids(cls, request: Request, ids: str, repository, model,
                                    session: AsyncSession,):
        """ Получение списка элементов для api view """
        if not ids:
            return []
        comma_separator = ','
        ids_set = tuple(int(b) for a in set(ids.split(comma_separator)) if (b := a.strip()).isdigit())
        items = await repository.get_by_ids(ids_set, model, session)
        default_image_id = get_default_image(request, 1)  # заглушка для thumbnails
        result = cls.convert_list_api_view(request, items, default_image_id)
        return result

    @classmethod
    async def execute_smart_search(cls, request, Request, query: str, session: AsyncSession,
                                   boost: float = 15.0,
                                   limit: int = 20,
                                   penalty: float = 0.1):
        # items = await super().execute_smart_search(query, session, boost, limit)
        # raw = query
        default_image_id = get_default_image(request, 1)
        query = query.replace('+', ' ')
        items: List[dict] = await super().search_by_hash(query, Item, ItemRepository, session, limit, boost, penalty)
        result = [transform_api_list_view(item, def_lang, cls.lang_suffix_list(language), default_image_id) for item in items]
        return result
