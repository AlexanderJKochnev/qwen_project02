# app.support.item.service.py
import asyncio
from functools import reduce
from typing import Any, Dict, List, Optional, Type, Union

from deepdiff import DeepDiff
# from sqlalchemy.sql.elements import Label
from fastapi import BackgroundTasks, HTTPException
from loguru import logger
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.utils.pydantic_utils import list_dict, inst_dict
from app.core.config.project_config import settings
from app.core.utils.backgound_tasks import background
from app.core.hash_norm import get_cached_hash, get_hashes_for_item, tokenize
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.services.service import Service
from app.core.types import ModelType
from app.core.utils.alchemy_utils import transform, transform_list_view
from app.core.utils.common_utils import flatten_dict_with_localized_fields, jprint, \
    localized_field_with_replacement  # , delta_data
from app.core.utils.converters import list_move, read_convert_json
from app.core.utils.pydantic_utils import get_field_name, make_paginated_response
from app.core.utils.reindexation import extract_text_ultra_fast
# from app.core.schemas.base import PaginatedResponse
from app.mongodb.service import ThumbnailImageService
from app.support import Drink, Item
from app.support.drink.repository import DrinkRepository
from app.support.drink.schemas import DrinkCreate, DrinkUpdate
from app.support.drink.service import DrinkService
from app.support.wordhash.model import WordHash
from app.support.item.repository import ItemRepository
from app.support.item.schemas import (ItemCreate, ItemCreatePreact, ItemCreateRelation, ItemDetailManyToManyLocalized,
                                      ItemListView, ItemRead, ItemReadRelation, ItemUpdate,
                                      ItemUpdatePreact)  # ItemApiLangNonLocalized, ItemApiLangLocalized, ItemApiLang,

_REINDEX_LOCK = asyncio.Lock()


itemdetailmanytomanylocalized = get_field_name(ItemDetailManyToManyLocalized)
ItemListViewAdapter: TypeAdapter = TypeAdapter(List[ItemListView])


class ItemService(Service):
    default = ['vol', 'drink_id', 'image_id']
    BATCH_SIZE = 1500  # Оптимально для баланса память/скорость

    @classmethod
    def _level_up_(cls, lang_prefixes: list, item: dict) -> dict:
        """
            внутренний метод
            перенос вложенных словарей на верхний уровень (drink -> item)
        """
        try:
            extra = [f'description{lang}' for lang in lang_prefixes]
            if drink := item.pop('drink'):
                drink.pop('id', None)
                # вложенные в drink словари тоже на верхний уровень
                for key in ('subcategory.category', 'site.subregion.region', 'site.subregion.region.country'):
                    tmp = drink
                    for k in key.split('.'):
                        tmp = tmp.get(k)
                    for x in extra:
                        tmp.pop(x, None)
                    drink[k] = tmp
                item.update(drink)
            return item
        except Exception as e:
            logger.error(f'app.support.item.service._level_up_.error: {e}')

    @classmethod
    def add_manytomany_fields(cls, item: dict, lang_prefixes: list) -> dict:
        """
            добавляет food и varietals в api и detail views
        """
        try:
            dict_lang: dict = {}
            for field in itemdetailmanytomanylocalized:
                match field:
                    case 'pairing':
                        pairing: list = []
                        tmp: list = item.get('food_associations')
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
            print(f'add_manytomany_fields.{e}')
            print(f"{item.get('foods')=} food")
            print(f"{item.get('varietal_associations')=} varietalds")
            return None

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
        DELETE
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
        lang_prefixes: list = cls.lang_suffix_list(language)
        drink_dict = item.get('drink')
        for key in localized_fields:
            match key:
                case 'country':
                    keys = ['site', 'subregion', 'region', 'country']
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
    async def get_list_view(cls, lang: str,
                            repository: Type[ItemRepository],
                            model: Type[Item], session: AsyncSession,
                            limit: int = 20):
        """Получение списка элементов для ListView с локализацией"""
        items: List[ModelType] = await repository.get_list_view(model, session, limit)
        items: List[Dict] = list_dict(items)
        language = cls.lang_sorted(lang)
        result = [transform_list_view(item, tuple(language)) for item in items]
        return result

    @classmethod
    async def get_list_view_page(cls, page: int, page_size: int,
                                 repository: ItemRepository, model: Item, session: AsyncSession,
                                 lang: str = 'en'):
        """Получение списка элементов для ListView с пагинацией и локализацией"""
        skip = (page - 1) * page_size
        items, total = await repository.get_list_view_page(skip, page_size, model, session)
        items: List[Dict] = list_dict(items)
        language = cls.lang_sorted(lang)
        result = [transform_list_view(item, tuple(language)) for item in items]
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def get_detail_view(cls, lang: str, id: int, repository: ItemRepository, model: Item, session: AsyncSession):
        """Получение детального представления элемента с локализацией"""
        item_instance = await repository.get_detail_view(id, model, session)
        # item: dict = item_instance.to_dict()
        item: dict = inst_dict(item_instance)
        if not item:    # если ничего нет
            return None
        # задаем порядок замещения пустых полей
        language = cls.lang_sorted(lang)
        item = transform(item, tuple(language))
        # список всех локализованных полей приложения
        return item

    @classmethod
    async def create_relation(cls, data: ItemCreateRelation, repository: ItemRepository,
                              model: Item, session: AsyncSession, **kwargs) -> ItemRead:
        kwargs['parent'] = 'drink'
        kwargs['parent_repo'] = DrinkRepository
        kwargs['parent_model'] = Drink
        kwargs['parent_service'] = DrinkService
        return super().create_relation(data, repository, model, session, **kwargs)

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
            raise Exception(e)

    @classmethod
    async def update_item_drink(cls, id: int, data: ItemUpdatePreact,
                                repository: ItemRepository,
                                model: Item, background_tasks: BackgroundTasks,
                                session: AsyncSession) -> Union[dict, None]:
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
            query = text("SELECT drink_id FROM items WHERE id = :id")
            res = await session.execute(query, {"id": item_id})
            drink_id = res.scalar()
            data_dict['drink_id'] = drink_id
            drink = DrinkUpdate(**data_dict)
            result = await DrinkService.patch(drink_id, drink, DrinkRepository, Drink, background_tasks,
                                              session)
            if not result.get('success'):
                raise HTTPException(status_code=500, detail=f'Не удалось обновить запись Drink {drink_id=}')
        # обновление item
        item = ItemUpdate(**data_dict)
        item_dict = item.model_dump()
        item_instance = await repository.get_by_id(item_id, model, session)
        if not item_instance:
            raise HTTPException(status_code=404, detail=f'Item records with {item_id=} not found')
        result = await repository.patch(item_instance, item_dict, session)
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
        items = list_dict(items)
        language = cls.lang_sorted(lang)
        result = [transform_list_view(item, tuple(language)) for item in items]
        return make_paginated_response(result, total, page, page_size)

    @classmethod
    async def search_by_trigram_index(cls, search_str: str, lang: str, repository: ItemRepository,
                                      model: Item, session: AsyncSession,
                                      page: int = None, page_size: int = None):
        """
            DEPRECATED
            Поиск элементов с использованием триграммного индекса в связанной модели Drink с локализацией
            при пустом поисковом запросе выдает ВСЕ ЗАПИСИ !! ЭТО ВАЖНО !! ТАК И ДОЛЖНО БЫТЬ !!!
        """
        skip = (page - 1) * page_size
        items, total = await repository.search_by_trigram_index(search_str, model, session, skip, page_size)
        language = cls.lang_sorted(lang)
        result = ItemListViewAdapter.validate_python([transform_list_view(item, tuple(language))
                                                      for item in items])
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
    async def get_by_idX(
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
        # item_dict: dict = await cls.get_by_id(id, repo, model, session)
        instance = await repo.get_by_id(id, model, session)
        if instance is None:
            raise HTTPException(status_code=404, detail=f'Запрашиваемый файл {id} не найден на сервере')
        # item_dict: dict = obj.to_dict()
        item_dict: dict = instance.to_dict_fast()
        drink: dict = item_dict.pop('drink')
        item_dict['drink_id'] = drink.pop('id')
        varietal_associations = drink.pop('varietal_associations', [])
        if varietal_associations:
            varietals = [{'id': item.get('varietal_id'), 'percentage': item.get('percentage')}
                         for item in varietal_associations if item]
            drink['varietals'] = varietals
        food_associations = drink.pop('food_associations', [])
        if food_associations:
            foods = [{'id': item.get('food_id')} for item in food_associations if item]
            drink['foods'] = foods
        item_dict.update(drink)
        return item_dict

    @classmethod
    async def search_geans_items(cls, lang: str, search: str, similarity_threshold: float,
                                 page: int, page_size: int,
                                 repository: Type[Repository], model: Type[Item], session: AsyncSession) -> List[dict]:
        """ новый поиск вместо триграмного  индекса ONLY FOR ITEMS_PREACT """
        try:
            # значение similarity_thresholfd настраивается в .env
            # similarity_threshold = similarity_threshold or settings.SIMILARITY_THRESHOLD
            # response = await cls.search_geans(search, similarity_threshold,
            #                                   page, page_size, repository, model, session)
            response = await cls.search_fts(search, page, page_size, repository, model, session)
            items = response.pop('items')
            total = response.get('total')
            if total == 0:
                result = []
            else:
                language = cls.lang_sorted(lang)
                result = ItemListViewAdapter.validate_python([transform_list_view(item, tuple(language))
                                                              for item in items])
            response = make_paginated_response(result, total, page, page_size)
            return response
        except Exception as e:
            logger.error(f'search_geans. {e}')
            raise HTTPException(status_code=502, detail=f'search_geans_items. {e}')

    @classmethod
    async def search_geans_all_items(cls, lang: str, search: str, similarity_threshold: float,
                                     repository: Type[Repository], model: ModelType,
                                     session: AsyncSession) -> List[dict]:
        try:
            # similarity_threshold = similarity_threshold or settings.SIMILARITY_THRESHOLD
            # items: list = await cls.search_geans_all(search, similarity_threshold,
            #                                          repository, model, session)
            items: list[dict] = await cls.search_fts_all(search, repository, model, session)
            language = cls.lang_sorted(lang)
            result = ItemListViewAdapter.validate_python(
                [transform_list_view(item, tuple(language)) for item in items]
            )
            return result
        except Exception as e:
            logger.error(f'search_gens_all. {e}')
            raise HTTPException(status_code=503, detail=f'search_gens_all. {e}')

    @classmethod
    @background
    async def run_reindex_worker(cls, session_factory, force_all: bool = False):
        async with session_factory() as session:
            # 1. Получаем СТРИМ всех ID и контента, которые нужно обновить
            # Это гарантирует, что мы пройдем по списку ОДИН РАЗ
            stmt = select(Item).options(selectinload(Item.drink))
            if not force_all:
                stmt = stmt.where(or_(Item.word_hashes == None, func.cardinality(Item.word_hashes) == 0))

            result_stream = await session.stream(stmt)
            batch_count = 0
            async for row in result_stream:
                item = row[0]
                if item.drink:
                    drink_dict = item.drink.to_dict()
                    content = extract_text_ultra_fast(drink_dict, cls.skip_keys)

                    # Твоя логика
                    item.search_content = content.lower()
                    item.word_hashes = get_hashes_for_item(content)

                    batch_count += 1

                # Коммитим каждые 1500 записей
                if batch_count >= cls.BATCH_SIZE:
                    await session.commit()
                    logger.info(f"Зафикисирован батч: {cls.BATCH_SIZE} записей")
                    batch_count = 0
                    # После коммита объекты в сессии инвалидируются,
                    # стрим продолжит работу со следующими

            await session.commit()  # финальный остаток
            logger.success('индексация завершена')

    @staticmethod
    async def execute_smart_search(query: str, session: AsyncSession, boost: float = 15.0, limit: int = 20) -> List[dict]:
        # 1. Токенизация и сбор хешей (включая префикс последнего слова)
        repo = ItemRepository
        tokens = tokenize(query)
        if not tokens:
            return []

        # Для простоты считаем все слова полными + ищем префиксы для последнего
        search_hashes = [get_cached_hash(t) for t in tokens]
        last_word_prefixes = await repo.get_hashes_by_prefix(session, tokens[-1])
        all_target_hashes = list(set(search_hashes) | set(last_word_prefixes))

        # 2. Получаем статистику частотности для весов
        stats_stmt = select(WordHash.hash, WordHash.freq).where(WordHash.hash.in_(all_target_hashes))
        stats_res = await session.execute(stats_stmt)
        word_stats = [{"hash": r[0], "freq": r[1]} for r in stats_res.all()]

        # 3. Финальный поиск
        return await repo.find_items_weighted_v2(session, word_stats, boost, limit)
