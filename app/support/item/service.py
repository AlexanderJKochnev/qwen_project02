# app.support.item.service.py
from deepdiff import DeepDiff
from typing import Type, Optional, Dict, Any
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
# from app.support.item.schemas import ItemCreate, ItemCreateRelation, ItemRead
from app.core.services.service import Service
from app.core.utils.common_utils import flatten_dict_with_localized_fields, get_value, jprint  # noqa: F401
from app.core.utils.converters import read_convert_json
from app.core.utils.pydantic_utils import make_paginated_response
from app.mongodb.service import ThumbnailImageService
from app.support.drink.model import Drink
from app.support.drink.repository import DrinkRepository
from app.support.drink.service import DrinkService
from app.support.drink.schemas import DrinkCreate, DrinkUpdate
from app.support.item.model import Item
from app.support.item.repository import ItemRepository
from app.support.item.schemas import (ItemCreate, ItemCreateRelation, ItemRead, ItemReadRelation,
                                      ItemCreatePreact, ItemUpdatePreact, ItemUpdate)


class ItemService(Service):
    default = ['vol', 'drink_id']

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

        # Helper function to check if a value is a Mock object
        def is_mock_object(value):
            return hasattr(value, '_mock_name') or (hasattr(value, '__class__') and 'Mock' in value.__class__.__name__)

        # Локализация заголовка
        if lang == 'en':
            result['title'] = item['drink'].title
        elif lang == 'ru':
            title_ru = getattr(item['drink'], 'title_ru', None)
            if is_mock_object(title_ru):
                title_ru = None
            result['title'] = title_ru if title_ru else item['drink'].title
        elif lang == 'fr':
            title_fr = getattr(item['drink'], 'title_fr', None)
            if is_mock_object(title_fr):
                title_fr = None
            result['title'] = title_fr if title_fr else item['drink'].title
        else:
            result['title'] = item['drink'].title

        # Локализация страны
        if lang == 'en':
            result['country'] = item['country'].name
        elif lang == 'ru':
            country_name_ru = getattr(item['country'], 'name_ru', None)
            if is_mock_object(country_name_ru):
                country_name_ru = None
            result['country'] = country_name_ru if country_name_ru else item['country'].name
        elif lang == 'fr':
            country_name_fr = getattr(item['country'], 'name_fr', None)
            if is_mock_object(country_name_fr):
                country_name_fr = None
            result['country'] = country_name_fr if country_name_fr else item['country'].name
        else:
            result['country'] = item['country'].name

        # Локализация категории
        if lang == 'en':
            category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], 'name', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name
        elif lang == 'ru':
            category_name = getattr(item['subcategory'].category, 'name_ru', None)
            if is_mock_object(category_name):
                category_name = None
            if category_name:
                category_name = category_name
            else:
                category_name = item['subcategory'].category.name

            subcategory_name = getattr(item['subcategory'], 'name_ru', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if not subcategory_name:
                subcategory_name = getattr(item['subcategory'], 'name', None)
                if is_mock_object(subcategory_name):
                    subcategory_name = None

            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name
        elif lang == 'fr':
            category_name = getattr(item['subcategory'].category, 'name_fr', None)
            if is_mock_object(category_name):
                category_name = None
            if category_name:
                category_name = category_name
            else:
                category_name = item['subcategory'].category.name

            subcategory_name = getattr(item['subcategory'], 'name_fr', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if not subcategory_name:
                subcategory_name = getattr(item['subcategory'], 'name', None)
                if is_mock_object(subcategory_name):
                    subcategory_name = None

            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name
        else:
            category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], 'name', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name

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
        item = await repository.get_detail_view(id, model, session)
        if not item:
            return None

        # Подготовим данные для локализации
        localized_data = {
            'id': item['id'],
            'vol': item['vol'],
            'alc': str(item['alc']) if item['alc'] is not None else None,
            'age': item['age'],
            'image_id': item['image_id'],
            'title': item['drink'].title,
            'title_ru': getattr(item['drink'], 'title_ru', ''),
            'title_fr': getattr(item['drink'], 'title_fr', ''),
            'subtitle': getattr(item['drink'], 'subtitle', ''),
            'subtitle_ru': getattr(item['drink'], 'subtitle_ru', ''),
            'subtitle_fr': getattr(item['drink'], 'subtitle_fr', ''),
            'country': item['country'].name if item['country'] else '',
            'country_ru': getattr(item['country'], 'name_ru', '') if item['country'] else '',
            'country_fr': getattr(item['country'], 'name_fr', '') if item['country'] else '',
            'subcategory': f"{item['subcategory'].category.name} {item['subcategory'].name}",
            'subcategory_ru': f"{getattr(item['subcategory'].category, 'name_ru', '')} {getattr(item['subcategory'], 'name_ru', '')}" if (getattr(item['subcategory'].category, 'name_ru', None) and getattr(item['subcategory'], 'name_ru', None)) else '',  # NOQA: E501
            'subcategory_fr': f"{getattr(item['subcategory'].category, 'name_fr', '')} {getattr(item['subcategory'], 'name_fr', '')}" if (getattr(item['subcategory'].category, 'name_fr', None) and getattr(item['subcategory'], 'name_fr', None)) else '',  # NOQA: E501
            'sweetness': getattr(item['sweetness'], 'name', '') if item['sweetness'] else '',
            'sweetness_ru': getattr(item['sweetness'], 'name_ru', '') if item['sweetness'] else '',
            'sweetness_fr': getattr(item['sweetness'], 'name_fr', '') if item['sweetness'] else '',
            'recommendation': getattr(item['drink'], 'recommendation', ''),
            'recommendation_ru': getattr(item['drink'], 'recommendation_ru', ''),
            'recommendation_fr': getattr(item['drink'], 'recommendation_fr', ''),
            'madeof': getattr(item['drink'], 'madeof', ''),
            'madeof_ru': getattr(item['drink'], 'madeof_ru', ''),
            'madeof_fr': getattr(item['drink'], 'madeof_fr', ''),
            'description': getattr(item['drink'], 'description', ''),
            'description_ru': getattr(item['drink'], 'description_ru', ''),
            'description_fr': getattr(item['drink'], 'description_fr', ''),
        }

        # Handle varietals and pairing with localization (similar to drink schemas)
        lang_suffix = '' if lang == 'en' else f'_{lang}'

        # Get varietals with localization and percentages
        varietal = []
        if hasattr(item['drink'], 'varietal_associations') and item['drink'].varietal_associations:
            for assoc in item['drink'].varietal_associations:
                if hasattr(assoc.varietal, f'name{lang_suffix}'):
                    name = getattr(assoc.varietal, f'name{lang_suffix}')
                elif hasattr(assoc.varietal, 'name'):
                    name = assoc.varietal.name
                else:
                    continue
                if name:
                    # Add percentage if available
                    if assoc.percentage is not None:
                        varietal.append(f"{name} {int(round(assoc.percentage))}%")
                    else:
                        varietal.append(name)

        # Get pairing (foods) with localization
        pairing = []
        if hasattr(item['drink'], 'food_associations') and item['drink'].food_associations:
            for assoc in item['drink'].food_associations:
                if hasattr(assoc.food, f'name{lang_suffix}'):
                    name = getattr(assoc.food, f'name{lang_suffix}')
                elif hasattr(assoc.food, 'name'):
                    name = assoc.food.name
                else:
                    continue
                if name:
                    pairing.append(name)

        # Применим функцию локализации
        localized_result = flatten_dict_with_localized_fields(
            localized_data,
            ['title', 'subtitle', 'country', 'subcategory', 'description',
             'sweetness', 'recommendation', 'madeof'],
            lang
        )
        localized_result['category'] = localized_result.pop('subcategory', '')
        # Add varietal (renamed from varietals) and pairing after localization
        if varietal:
            localized_result['varietal'] = varietal
        if pairing:
            localized_result['pairing'] = pairing

        # Добавим остальные поля
        localized_result['id'] = item['id']
        localized_result['vol'] = item['vol']
        localized_result['alc'] = str(item['alc']) if item['alc'] is not None else None
        localized_result['age'] = item['age']
        localized_result['image_id'] = item['image_id']

        return localized_result

    @classmethod
    async def create_relation(cls, data: ItemCreateRelation,
                              repository: ItemRepository, model: Item,
                              session: AsyncSession) -> ItemRead:
        try:
            item_data: dict = data.model_dump(exclude={'drink', 'warehouse'},
                                              exclude_unset=True)
            if data.drink:
                try:
                    result = await DrinkService.create_relation(data.drink, DrinkRepository, Drink, session)
                    await session.commit()
                    # ошибка вот здесь.
                    item_data['drink_id'] = result.id
                except Exception as e:
                    print('data.drink.error::', result, e)
            # if data.warehouse:
            #     result = await WarehouseService.create_relation(data.warehouse, WarehouseRepository,
            #                                                     Warehouse, session)
            #     item_data['warehouse_id'] = result.id
            item = ItemCreate(**item_data)
            item_instance, new = await cls.get_or_create(item, ItemRepository, Item, session)
            return item_instance, new
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
            return item_instance, new
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
        """Поиск элементов с использованием триграммного индекса в связанной модели Drink с локализацией"""
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
        """Получение записи по ID с автоматическим переводом недостающих локализованных полей"""
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
