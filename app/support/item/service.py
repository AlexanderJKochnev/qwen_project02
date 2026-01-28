# app.support.item.service.py
from deepdiff import DeepDiff
from datetime import datetime
from functools import reduce
# import json
from decimal import Decimal
from typing import Type, Optional, Dict, Any
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
# from app.support.item.schemas import ItemCreate, ItemCreateRelation, ItemRead
from app.core.services.service import Service
from app.core.config.project_config import settings
from app.core.utils import localized_field_with_replacement
from app.core.utils.pydantic_utils import get_field_name
from app.core.utils.common_utils import flatten_dict_with_localized_fields, camel_to_enum, jprint
from app.core.utils.converters import read_convert_json, list_move, lang_suffix_list, lang_suffix_dict
from app.core.utils.pydantic_utils import make_paginated_response
from app.core.models.outbox_model import OutboxAction
from app.mongodb.service import ThumbnailImageService
from app.support.drink.model import Drink
from app.support.drink.repository import DrinkRepository
from app.support.drink.service import DrinkService
from app.support.drink.schemas import DrinkCreate, DrinkUpdate
from app.support.item.model import Item
from app.support.item.repository import ItemRepository
from app.support.item.schemas import (ItemCreate, ItemCreateRelation, ItemRead, ItemReadRelation,
                                      ItemCreatePreact, ItemUpdatePreact, ItemUpdate,
                                      ItemDetailNonLocalized, ItemDetailLocalized, ItemDetailForeignLocalized,
                                      ItemDetailManyToManyLocalized, ItemListView,
                                      ItemApiLangNonLocalized, ItemApiLangLocalized, ItemApiLang, ItemApi)


class ItemService(Service):
    default = ['vol', 'drink_id']

    @classmethod
    def _level_up_(cls, lang_prefixes: list, item: dict) -> dict:
        """
            внутренний метод
            перенос вложенных словарей на верхний уровень (drink -> item)
        """
        extra = [f'description{lang}' for lang in lang_prefixes]
        if drink := item.pop('drink'):
            drink.pop('id', None)
            # вложенные в drink словари тоже на верхний уровень
            for key in ('subcategory.category', 'subregion.region', 'subregion.region.country'):
                tmp = drink
                for k in key.split('.'):
                    tmp = tmp.get(k)
                for x in extra:
                    tmp.pop(x, None)
                drink[k] = tmp
            item.update(drink)
        return item

    @classmethod
    def __add_manytomany_fields__(cls, item: dict, lang_prefixes: list) -> dict:
        """
        добавляет foods и varietals в api и detail views
        items.keys():
            'drink_id',
            'vol',
            'created_at',
            'image_path',
            'price', 'count',
            'id',
            'image_id',
            'sugar',
            'sweetness_id',
            'subtitle_ru',
            'madeof',
            'age',
            'subtitle_fr',
            'madeof_ru',
            'description',
            'madeof_fr',
            'description_ru',
            'title',
            'description_fr',
            'sparkling',
            'title_ru',
            'recommendation',
            'alc',
            'subcategory_id',
            'title_fr',
            'recommendation_ru',
            'subregion_id',
            'subtitle',
            'recommendation_fr',
            'subcategory',
            'foods',
            'varietal_associations',
            'subregion',
            'sweetness',
            'items',
            'category',
            'region',
            'country',
            'changed_at'
        """
        try:
            dict_lang: dict = {}
            for field in get_field_name(ItemDetailManyToManyLocalized):
                match field:
                    case 'pairing':
                        pairing: list = []
                        tmp: list = item.get('foods')
                        if tmp and isinstance(tmp, (list, tuple)) and tmp != [None]:
                            for food_dict in tmp:
                                if tf := localized_field_with_replacement(food_dict, 'name', lang_prefixes, 'food'):
                                    pairing.append(tf.get('food'))
                        dict_lang.update({'pairing': pairing})
                    case 'varietal':
                        tmp = item.get('varietal_associations')
                        varietal: list = []
                        if tmp and isinstance(tmp, (list, tuple)) and tmp != [None]:
                            for varietal_dict in tmp:
                                if sf := varietal_dict.get('varietal'):
                                    if tf := localized_field_with_replacement(sf, 'name', lang_prefixes, 'varietal'):
                                        xf = tf.get('varietal')
                                        if percent := varietal_dict.get('percentage'):
                                            xf = f'{xf} {percent:.0f} %'
                                        varietal.append(xf)
                        dict_lang.update({'varietal': varietal})
                    case _:
                        pass  # do nothing
            return dict_lang
        except Exception as e:
            print(f'__add_manytomany_fields__.{e}')
            print(f"{item.get('foods')=} food")
            print(f"{item.get('varietal_associations')=} varietalds")
            return None

    @classmethod
    def __api_view__(cls, item: dict) -> dict:
        """ логика метода get_api_view """
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
        try:
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
                    if k == 'region':   # вложенные сущности
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
                many_to_many = cls.__add_manytomany_fields__(item, lang_suff)
                dict_lang.update(many_to_many)
                validated_result = ItemApiLang.model_validate(dict_lang)
                result[key] = validated_result.model_dump(exclude_none=True)
            validated_result = ItemApi.model_validate(result)
            return validated_result
        except Exception as e:
            print(f'__api_view__.error {e} {item.get("id")=}')
            raise HTTPException(status_code=500, detail=f'error.__api_view__.{e}')

    @classmethod
    def _process_item_localization(cls, item: dict, lang: str, fields_to_localize: list = None):
        """
            Внутренний метод для обработки локализации одного элемента
            на входе dict в котором один из элементов Drink
        """
        if fields_to_localize is None:
            fields_to_localize = ['title', 'country', 'subcategory']
        # Применим функцию локализации
        localized_result = flatten_dict_with_localized_fields(
            item,  # localized_data,
            fields_to_localize,
            lang
        )

        # Добавим остальные поля
        localized_result['id'] = item['id']
        localized_result['vol'] = item['vol']
        localized_result['image_id'] = item['image_id']

        return localized_result

    @classmethod
    def transform_item_for_list_view(cls, item: dict, lang: str = 'en'):
        """
        Преобразование элемента из текущего формата в требуемый для ListView

        :param item: Элемент в текущем формате (с вложенными объектами)
        :param lang: Язык локализации ('en', 'ru', 'fr')
        :return: Преобразованный элемент в требуемом формате
        """

        # Основные поля
        result = {
            'id': item['id'],
            'vol': item['vol'],
            'image_id': item['image_id']
        }
        # локализованные поля (если нужны нелокадизованные, всталяй их выше в result)
        localized_fields = [v for v in get_field_name(ItemListView) if v not in result.keys()]
        # задаем порядок замещения пустых полей
        language: list = list_move(settings.LANGUAGES, lang)
        lang_prefixes: list = lang_suffix_list(language)
        drink_dict = item.get('drink')
        for key in localized_fields:
            match key:
                case 'country':
                    keys = ['subregion', 'region', 'country']
                    value = reduce(lambda d, k: d.get(k) if isinstance(d, dict) else None, keys, drink_dict)
                    if isinstance(value, dict):
                        lf = localized_field_with_replacement(value, 'name', lang_prefixes, key)
                        result.update(lf)
                case 'category':
                    keys = ['subcategory', 'category']
                    value = reduce(lambda d, k: d.get(k) if isinstance(d, dict) else None, keys, drink_dict)
                    if isinstance(value, dict):
                        lf = localized_field_with_replacement(value, 'name', lang_prefixes, key)
                        if value.get('name').lower() == 'wine':
                            value = drink_dict.get('subcategory')
                            ls = localized_field_with_replacement(value, 'name', lang_prefixes, 'subcategory')
                            lf['category'] = f'{ls.get('subcategory')} {lf.get('category')}'
                        result.update(lf)
                case _:
                    value = drink_dict.get(key)
                    lf = localized_field_with_replacement(drink_dict, key, lang_prefixes)
                    result.update(lf)
        return result

    @classmethod
    async def get_list_view(cls, lang: str, repository: ItemRepository, model: Item, session: AsyncSession):
        """Получение списка элементов для ListView с локализацией"""
        items = await repository.get_list_view(model, session)
        result = []
        for item in items:
            transformed_item = cls.transform_item_for_list_view(item, lang)
            result.append(transformed_item)
        return result

    @classmethod
    async def get_list_view_page(cls, page: int, page_size: int,
                                 repository: ItemRepository, model: Item, session: AsyncSession,
                                 lang: str = 'en'):
        """Получение списка элементов для ListView с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.get_list_view_page(skip, page_size, model, session)
        result = []
        for item in items:
            transformed_item = cls.transform_item_for_list_view(item, lang)
            result.append(transformed_item)
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def get_detail_view(cls, lang: str, id: int, repository: ItemRepository, model: Item, session: AsyncSession):
        """Получение детального представления элемента с локализацией"""
        item_instance = await repository.get_detail_view(id, model, session)
        item: dict = item_instance.to_dict()
        if not item:    # если ничего нет
            return None
        # задаем порядок замещения пустых полей
        language: list = list_move(settings.LANGUAGES, lang)
        lang_prefixes: list = lang_suffix_list(language)
        item = cls._level_up_(lang_prefixes, item)
        # список всех локализованных полей приложения
        result: dict = {}
        # добавление non-localized fields
        for key in get_field_name(ItemDetailNonLocalized):
            if val := item.get(key):
                if isinstance(val, (float, Decimal)):
                    val = f"{val:.03g}"
                result[key] = val
        # добавление localized fields
        for field in get_field_name(ItemDetailLocalized):
            if lf := localized_field_with_replacement(item, field, lang_prefixes):
                result.update(lf)
        # добавление foreign localized fields
        for field in get_field_name(ItemDetailForeignLocalized):
            if root := item.get(field):
                if lf := localized_field_with_replacement(root, 'name', lang_prefixes, field):
                    result.update(lf)
        # добавление manytomany fields
        many_to_many = cls.__add_manytomany_fields__(item, lang_prefixes)
        """
        for field in get_field_name(ItemDetailManyToManyLocalized):
            match field:
                case 'pairing':
                    if tmp := item.get('food_associations'):
                        pairing = []
                        for food_dict in tmp:
                            if sf := food_dict.get('food'):
                                if tf := localized_field_with_replacement(sf, 'name', lang_prefixes, 'food'):
                                    pairing.append(tf.get('food'))
                        if pairing:
                            result.update({'pairing': pairing})
                case 'varietal':
                    if tmp := item.get('varietal_associations'):
                        varietal = []
                        for varietal_dict in tmp:
                            if sf := varietal_dict.get('varietal'):
                                if tf := localized_field_with_replacement(sf, 'name', lang_prefixes, 'varietal'):
                                    xf = tf.get('varietal')
                                    if percent := varietal_dict.get('percentage'):
                                        xf = f'{xf} {percent:.0f} %'
                                    varietal.append(xf)
                        if varietal:
                            result.update({'varietal': varietal})
                case _:
                    pass
                    # do nothing"""
        result.update(many_to_many)
        return result

    @classmethod
    async def create_relation(cls, data: ItemCreateRelation,
                              repository: ItemRepository, model: Item,
                              session: AsyncSession, **kwargs) -> ItemReadRelation:
        try:
            item_data: dict = data.model_dump(exclude={'drink', 'warehouse'},
                                              exclude_unset=True)
            if data.drink:
                try:
                    result = await DrinkService.create_relation(data.drink, DrinkRepository, Drink, session)
                    # await session.commit()
                    item_data['drink_id'] = result.id
                except Exception as e:
                    print('data.drink.error::', result, e)
            # if data.warehouse:
            #     result = await WarehouseService.create_relation(data.warehouse, WarehouseRepository,
            #                                                     Warehouse, session)
            #     item_data['warehouse_id'] = result.id
            item = ItemCreate(**item_data)
            item_instance, new = await cls.get_or_create(item, ItemRepository, Item, session)
            # id = item_instance.id
            # await session.commit()
            await cls._queue_meili_sync(session, model, repository, OutboxAction.CREATE, item_instance)
            if kwargs.get('commit'):
                await session.commit()
            else:
                await session.flush()
                await session.refresh(item_instance)
            return item_instance  # new
        except Exception as e:
            raise Exception(f'itemservice.create_relation. {e}')

    @classmethod
    async def create_item_drink(cls, data: ItemCreatePreact,
                                repository: ItemRepository, model: Item,
                                session: AsyncSession) -> ItemRead:
        """
            item_drink_data, ItemRepository, Item, session
        """
        try:
            data_dict = data.model_dump(exclude_unset=True)
            drink = DrinkCreate(**data_dict)
            result, created = await DrinkService.create(drink, DrinkRepository, Drink, session)
            data_dict["drink_id"] = result.id
            item = ItemCreate(**data_dict)
            item_instance, new = await cls.get_or_create(item, ItemRepository, Item, session)
            return item_instance
        except Exception as e:
            raise Exception(f'item_create_item_drink_error: {e}')

    @classmethod
    async def update_item_drink(cls, id: int, data: ItemUpdatePreact,
                                isfile: bool, repository: ItemRepository,
                                model: Item, session: AsyncSession) -> ItemRead:
        """
            обновление item, включая drink
        """
        data_dict = data.model_dump()
        item_id = id
        if data.drink_action == 'create':
            drink = DrinkCreate(**data_dict)
            result, created = await DrinkService.create(drink, DrinkRepository, Drink, session)
            data_dict["drink_id"] = result.id
        else:
            drink_id = data_dict.get('drink_id')
            drink = DrinkUpdate(**data_dict)
            result = await DrinkService.patch(drink_id, drink, DrinkRepository, Drink, session)
            if not result.get('success'):
                raise HTTPException(status_code=500, detail=f'Не удалось обновить запись Drink {drink_id=}')
        item = ItemUpdate(**data_dict)
        if isfile:
            item_dict = item.model_dump()
        else:
            item_dict = item.model_dump(exclude=['image_id', 'image_path'])
        item_instance = await repository.get_by_id(item_id, Item, session)
        if not item_instance:
            raise HTTPException(f'Item records with {item_id=} not found')
        result = await repository.patch(item_instance, item_dict, session)
        """ will be return:
                    {"success": True, "data": obj}
                    or
                    {"success": False,
                     "error_type": "unique_constraint_violation",
                     "message": f"Нарушение уникальности: {original_error_str}",
                     "field_info": field_info... !this field is Optional
                     }
                """
        return result

    @classmethod
    async def search_by_drink_title_subtitle(cls, search_str: str, lang: str,
                                             repository: ItemRepository, model: Item,
                                             session: AsyncSession,
                                             page: int = None, page_size: int = None):
        """Поиск элементов по полям title* и subtitle* связанной модели Drink с локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.search_by_drink_title_subtitle(search_str,
                                                                       session,
                                                                       skip,
                                                                       page_size)
        result = []
        for item in items:
            transformed_item = cls.transform_item_for_list_view(item, lang)
            result.append(transformed_item)
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def search_by_trigram_index(cls, search_str: str, lang: str, repository: ItemRepository,
                                      model: Item, session: AsyncSession,
                                      page: int = None, page_size: int = None):
        """
            Поиск элементов с использованием триграммного индекса в связанной модели Drink с локализацией
            при пустом поисковом запросе выдает ВСЕ ЗАПИСИ !! ЭТО ВАЖНО !! ТАК И ДОЛЖНО БЫТЬ !!!
        """
        # if search_str is None:
        #     return None  # make_paginated_response([], 0, page, page_size)
        skip = (page - 1) * page_size
        items, total = await repository.search_by_trigram_index(search_str, model, session, skip, page_size)
        result = []
        for item in items:
            transformed_item = cls.transform_item_for_list_view(item, lang)
            result.append(transformed_item)
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def direct_upload(cls, file_name: dict, session: AsyncSession, image_service: ThumbnailImageService) -> dict:
        try:
            # получаем список кортежей (image_name, image_id)
            result: dict = {'total_input': 0,
                            'count_of_added_records': 0,
                            'error': [],
                            'error_nmbr': 0}
            # image_list = await image_service.get_images_list_after_date()
            for n, data in read_convert_json(file_name):
                result['total_input'] = result.get('total_input', 0) + 1
                instance = ItemCreateRelation.validate(data)
                # присваиваем значение image_id
                image_path = instance.image_path
                image_id = await image_service.get_id_by_filename(image_path)
                if not image_id:
                    raise Exception(f'{image_path=}======')
                instance.image_id = image_id
                data = instance.model_dump(exclude_unset=True, exclude_none=True)
                try:
                    new_instance, new = await cls.create_relation(instance, ItemRepository, Item, session)
                    new_instance = await cls.get_by_id(new_instance.id, ItemRepository, Item, session)
                    new1 = ItemReadRelation.validate(new_instance)
                    new2 = new1.model_dump(exclude_unset=True, exclude_none=True)
                    diff = DeepDiff(new2, data,
                                    exclude_paths=["root['price']", "root['id']",
                                                   "root['drink']['id']",
                                                   "root['drink']['foods']",
                                                   "root['drink']['varietals']"]
                                    )
                    if diff:
                        print('исходные данные')
                        jprint(data)
                        print('сохраненный результат')
                        jprint(new2)
                        raise Exception(f'Ошибка сохранения записи uid {data.get("image_path")}'
                                        f'{diff}')
                    result['count_of_added_records'] = result.get('count_of_added_records', 0) + int(new)
                except ValidationError as exc:
                    jprint(data)
                    for error in exc.errors():
                        print(f"  Место ошибки (loc): {error['loc']}")
                        print(f"  Сообщение (msg): {error['msg']}")
                        print(f"  Тип ошибки (type): {error['type']}")
                        # input_value обычно присутствует в словаре ошибки
                        if 'input_value' in error:
                            print(f"  Некорректное значение (input_value): {error['input_value']}")
                        print("-" * 20)
                    assert False, 'ошибка валидации в методе ItemService.direct_upload'
                except Exception as e:
                    print(f'error: {e}')
                    result['error'] = result.get('error', []).append(instance.image_path)
                    result['error_nmbr'] = len(result.get('error', 0))
            return result
        except Exception as exc:
            print(f'{exc=}')

    @classmethod
    async def search_items_orm_paginated_async(cls, query_str: str, lang: str,
                                               repository: ItemRepository,
                                               model: Item,
                                               session: AsyncSession,
                                               page: int = 1,
                                               page_size: int = 20
                                               ):
        """ Получение списка элементов для ListView с пагинацией и локализацией
            session: AsyncSession,
            query_string: str,
            page_size: int,
            page: int  # Номер страницы (начиная с 1)
        """
        items, total = await repository.search_items_orm_paginated_async(query_str, session,
                                                                         page_size, page)
        result = []
        for item in items:
            tmp = item.to_dict()
            localized_result = cls._process_item_localization(tmp, lang)
            result.append(localized_result)
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def get_by_id(
            cls, id: int, repository: Type[ItemRepository], model: Type[Item], session: AsyncSession
    ) -> Optional[ItemRead]:
        """Получение записи по ID"""
        result = await repository.get_by_id(id, model, session)
        return result

    @classmethod
    async def get_one(cls,
                      id: int,
                      session: AsyncSession) -> Dict[str, Any]:
        """
            Получение одной записи по ID
        """
        repo = ItemRepository
        model = Item
        obj = await cls.get_by_id(id, repo, model, session)
        if obj is None:
            raise HTTPException(status_code=404, detail=f'Запрашиваемый файл {id} не найден на сервере')
        item_dict: dict = obj.to_dict()
        drink = obj.drink

        varietal_associations = drink.varietal_associations
        varietals = [{'id': item.varietal_id, 'percentage': item.percentage}
                     for item in varietal_associations if item]
        food_associations = drink.food_associations
        foods = [{'id': item.food_id} for item in food_associations if item]
        drink_dict = drink.to_dict()
        item_dict['drink_id'] = drink.id
        if varietals:
            drink_dict.pop('varietals', None)
            drink_dict['varietals'] = varietals
        if foods:
            drink_dict.pop('foods', None)
            drink_dict['foods'] = foods
        tmp = DrinkCreate(**drink_dict)
        drink_dict = tmp.model_dump(exclude_unset=True, exclude_none=True)
        item_dict.update(drink_dict)
        return item_dict

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
        jprint(result)
        return result

    @classmethod
    async def get_list_api_view(cls, after_date: datetime, repository, model,
                                session: AsyncSession,):
        """ Получение списка элементов для api view """
        items = await repository.get(after_date, model, session)
        result = []
        for item in items:
            if item_dict := item.to_dict():
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
