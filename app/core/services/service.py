# app.core.service/service.py
import asyncio
import math
from abc import ABCMeta
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from fastapi import BackgroundTasks, HTTPException
from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import or_

from app.core.config.database.db_async import DatabaseManager
from app.core.config.project_config import settings
from app.core.hash_norm import get_cached_hash, tokenize
from app.core.models.base_model import Base, get_model_by_name
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.schemas.base import BaseModel, IndexFillResponse
from app.core.services.click_service import FullTextSearch
from app.core.types import ModelType
from app.core.utils.alchemy_utils import formatted_query, has_column
from app.core.utils.common_utils import flatten_dict_with_localized_fields, make_paging_dict
from app.core.utils.pydantic_utils import (get_data_for_search, get_repo,
                                           make_paginated_response, prepare_search_string, inst_dict, list_dict)
from app.core.utils.reindexation import extract_text_ultra_fast, reindex_items
from app.mongodb.service import ThumbnailImageService
from app.service_registry import get_search_dependencies, register_service

# from app.core.utils.common_utils import jprint

joint = '. '
_REINDEX_LOCK = asyncio.Lock()
_reindex_task_lock = asyncio.Lock()
BATCH_SIZE = 500  # Оптимально для баланса память/скорость


class ServiceMeta(ABCMeta):

    def __new__(cls, name, bases, attrs):
        # if not hasattr(cls, '_registry'):
        #     cls._registry = {}

        new_class = super().__new__(cls, name, bases, attrs)
        # Регистрируем сам класс, а не его экземпляр
        if not attrs.get('__abstract__', False):
            key = name.lower().replace('service', '')
            register_service(key, new_class)
            # cls._registry[key] = new_class  # ← Сохраняем класс!
            # print(f"✅ Зарегистрирован сервис: {name} -> ключ: '{key}'")
        return new_class


class Service(metaclass=ServiceMeta):
    """
        Base Service Layer
    """
    __abstract__ = True
    #  список уникальных полей по которым будет осуществляться поиск в методах
    #  список уникальных полей для get_or_create, update_or_create
    default: list = ['name']
    # список полей исключенных из fts индексации
    skip_keys = {'id', 'created_at', 'udated_at', 'alc', 'sugar', 'age', 'sparkling', 'subcategory_id', 'sweetness_id',
                 'source_id', 'producer_id', 'vintageconfig_id', 'classification_id', 'designation_id', 'site_id',
                 'parcel_id', 'category_id', 'drink_id', 'food_id', 'superfood_id', 'varietal_id', 'percentage'}

    @classmethod
    async def get_instance(cls, data_dict: dict, repository: Type[Repository], model: ModelType,
                           session: AsyncSession, default: List = None):
        """ получение instance дя методов get(update)_or_create"""
        # значения ключевых полей для поиска
        logger.info('gett_instance')
        if not default:
            default = cls.default
        lookup_dict = {key: val for key, val in data_dict.items() if key in default}
        # поиск существующей записи по совпадению объектов по уникальным полям
        instance = await repository.get_by_fields(lookup_dict, model, session)
        return instance

    @classmethod
    async def create(cls, data: BaseModel, repository: Repository, model: ModelType,
                     session: AsyncSession, **kwargs) -> ModelType:
        """ create & return record """
        # удаляет пустые поля
        data_dict = data.model_dump(exclude_unset=True)
        obj = model(**data_dict)
        if model.__name__ == 'Item':
            drink_model = get_model_by_name('Drink')
            drink_repo = get_repo('Drink')
            # создагние индекса налету
            obj = await reindex_items(obj, drink_model, drink_repo, cls.skip_keys, session)
        result = await repository.create(obj, model, session)
        await session.commit()
        return inst_dict(result)

    @classmethod
    async def get_or_create(cls, data: Union[BaseModel, dict], repository: Repository,
                            model: Type[ModelType], session: AsyncSession,
                            default: List[str] = None, **kwargs) -> Tuple[ModelType, bool]:
        """
            находит или создaет запись
            возвращает instance и True (запись создана) или False (запись существует)
        """
        try:
            if default is None:
                default = cls.default
            if not isinstance(data, dict):
                # если исходные данные не словарь
                data_dict: dict = data.model_dump(exclude_unset=True)
            default_dict: dict = {key: val for key, val in data_dict.items() if key in default}
            instance: ModelType = await repository.get_by_fields(default_dict, model, session)
            if instance:
                return inst_dict(instance), False
            # запись не найдена
            obj = model(**data_dict)
            if model.__name__ == 'Item':
                drink_model = get_model_by_name('Drink')
                drink_repo = get_repo('Drink')
                # создание индексируемого поля на лету
                obj = await reindex_items(obj, drink_model, drink_repo, cls.skip_keys, session)
            instance = await repository.create(obj, model, session)
            await session.commit()
            return inst_dict(instance), True
        except IntegrityError as e:
            await session.rollback()
            raise Exception(f'Integrity error: {e}')
        except Exception as e:
            await session.rollback()
            raise Exception(f"UNKNOWN_ERROR: {str(e)}") from e

    @classmethod
    async def batch_get_or_create(cls, data_list: List[ModelType],
                                  repository: Type[Repository], model: ModelType,
                                  session: AsyncSession, default: List[str] = None, **kwargs) -> Tuple[ModelType, bool]:
        """
            находит или создaет записи из списка
            возвращает instance и True (запись создана) или False (запись существует)
        """
        try:
            if default is None:
                default = cls.default
            result: list = []
            for data in data_list:
                data_dict = data.model_dump(exclude_unset=True)
                default_dict = {key: val for key, val in data_dict.items() if key in default}
                # ошибка НУЖЕН ПОИСК ПО УНИКАЛЬНЫМ И СВЯЗАННЫМ ПОЛЯМ
                # поиск существующей записи по совпадению объектов по уникальным полям
                instance = await repository.get_by_fields(default_dict, model, session)
                if instance:
                    result.append(instance)
                else:
                    # запись не найдена
                    obj = model(**data_dict)
                    instance = await repository.create(obj, model, session)
                    result.append(instance)
            await session.commit()
            return list_dict(result)
        except IntegrityError as e:
            await session.rollback()
            raise Exception(f'Integrity error: {e}')
        except Exception as e:
            await session.rollback()
            raise Exception(f"UNKNOWN_ERROR: {str(e)}") from e

    @classmethod
    async def update_or_create(cls, data: BaseModel, repository: Type[Repository],
                               model: Type[ModelType], background_tasks: BackgroundTasks, session: AsyncSession,
                               default: List[str] = None, **kwargs) -> Tuple[Dict, bool]:
        """
            находит и обновляет запись или создает если ее нет.
            этим методом нельзя обновить ключевые поля - используй path + id
        """
        try:
            data_dict = data.model_dump(exclude_unset=True)
            instance = await cls.get_instance(data_dict, repository, model, session, default)
            # значения ключевых полей для поиска
            if not instance:
                # запись не найдена, добавляем
                obj = model(**data_dict)
                instance = await repository.create(obj, model, session)
                await session.commit()
                return instance, True
            # запись найдена, обновляем
            result = await cls.patch(instance, data, repository, model, background_tasks, session)
            if result.get('success'):
                return inst_dict(result.get('data')), False
            else:
                raise HTTPException(status_code=501, detail=f"{result.get('message')}")
        except Exception as e:
            logger.error(f'core.service.update_or_create.error {e}')
            raise Exception(e)

    @classmethod
    async def create_relation(cls, data: BaseModel,
                              repository: Repository, model: Type[ModelType], session: AsyncSession,
                              **kwargs) -> ModelType:
        """
            создание записей из json - со связями, если нет связей - просто get_or_create
        """
        parent: str = kwargs.get('parent')
        parent_repo = kwargs.get('parent_repo')
        parent_model = kwargs.get('parent_model')
        parent_service = kwargs.get('parent_service')
        # pydantic model -> dict & exclude parent
        data_dict: dict = data.model_dump(exclude={parent}, exclude_unset=True)
        # get parent pydantic model, get_or_create parent_id, add parent_id to data_dict
        if parent_data := getattr(data, parent):
            result, _ = await parent_service.get_or_create(parent_data, parent_repo, parent_model, session)
            data_dict[f'{parent}_id'] = result.id
        # get_or_create
        result, _ = await cls.get_or_create(data_dict, repository, model, session)
        return result

    @classmethod
    async def get(cls, ater_date: datetime,
                  page: int, page_size: int, repository: Type[Repository], model: ModelType,
                  session: AsyncSession) -> Dict[str, Any]:
        # Запрос с загрузкой связей и пагинацией
        try:
            skip = (page - 1) * page_size
            items, total = await repository.get(ater_date, skip, page_size, model, session)
            # items_dict = [item.to_dict_fast() for item in items]
            items_dict = list_dict(items)
            result = make_paginated_response(items_dict, total, page, page_size)
            return result
        except Exception as e:
            logger.error(f'get  {e}')

    @classmethod
    async def get_all(cls, after_date: datetime,
                      repository: Type[Repository], model: ModelType,
                      session: AsyncSession, limit: int = 20) -> Optional[List[ModelType]]:
        # Запрос с загрузкой связей -  возвращает список
        items: List[ModelType] = await repository.get_all(after_date, model, session, limit)
        return list_dict(items)
        # items_dict = [item.to_dict_fast() for item in items]
        # return items_dict

    @classmethod
    async def get_full(
        cls, repository: Type[Repository], model: ModelType, session: AsyncSession, limit: int = 20
    ) -> Optional[List[dict]]:
        # Запрос с загрузкой связей -  возвращает список
        result = await repository.get_full(model, session, limit)
        return list_dict(result)

    @classmethod
    async def get_full_with_pagination(
        cls, page: int, page_size: int, repository: Type[Repository], model: ModelType,
        session: AsyncSession
    ) -> Dict[str, Any]:
        # Запрос с загрузкой связей и пагинацией
        skip = (page - 1) * page_size
        items, total = await repository.get_full_with_pagination(skip, page_size, model, session)
        items = list_dict(items)
        result = make_paginated_response(items, total, page, page_size)
        return result

    @classmethod
    async def get_by_id(
            cls, id: int, repository: Type[Repository],
            model: ModelType, session: AsyncSession) -> Optional[Dict]:
        """Получение записи по ID с автоматическим переводом недостающих локализованных полей"""
        result = await repository.get_by_id(id, model, session)
        return inst_dict(result)

    @classmethod
    async def get_by_ids(cls, ids: str | List[int], repository: Type[Repository],
                         model: ModelType, session: AsyncSession) -> Optional[List[Dict]]:
        """
        получение набора записей по набору ids
        """
        result = []
        if ids:
            comma_separator = ','
            ids = tuple(int(b) for a in set(ids.split(comma_separator)) if (b := a.strip()).isdigit())
            result = await repository.get_by_ids(ids, model, session)
        return list_dict(result)

    @classmethod
    async def patch(cls, id: Union[int, Any], data: ModelType,
                    repository: Type[Repository],
                    model: ModelType,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession) -> Dict:
        """
        Редактирование записи по ID или instance
        Возвращает dict с результатом операции
        """
        if isinstance(id, int):
            # Получаем существующую запись
            existing_item: ModelType = await repository.get_by_id(id, model, session)
        else:
            # вместо id передан instance
            existing_item: ModelType = id
            id = existing_item.id
        data_dict = data.model_dump(exclude_unset=True)
        # Выполняем обновление
        result = await repository.patch(existing_item, data_dict, session)
        await cls.pre_run_background_task(id, background_tasks, repository, model)
        result['data'] = inst_dict(result.get('data'))
        return result

    @classmethod
    async def delete(cls, id: int, model: ModelType, repository: Type[Repository],
                     background_tasks: BackgroundTasks,
                     session: AsyncSession) -> bool:
        instance = await repository.get_by_id(id, model, session)
        resp = await repository.delete(instance, session)
        # здесь НЕ запускаем pre_run_background_task потому что
        # если есть зависимые записи - удалить не даст, а если нет - то search_source обновлять не где
        # patch достаточно
        # cls.pre_run_background_task(id, background_tasks, repository, model)
        return resp

    @classmethod
    async def search(cls, search: str, page: int, page_size: int,
                     repository: Type[Repository], model: ModelType,
                     session: AsyncSession
                     ) -> Dict[str, Any]:
        """
            базовый поиск
        """
        skip = (page - 1) * page_size
        items, total = await repository.search(search, skip, page_size, model, session)
        items = list_dict(items)
        result = make_paginated_response(items, total, page, page_size)
        return result

    @classmethod
    async def search_all(cls,
                         search: str,
                         repository: Type[Repository],
                         model: ModelType,
                         session: AsyncSession, limit: int = 20) -> List[Dict]:
        """
            базовый поиск без пагинации
        """
        result = await repository.search_all(search, model, session, limit)
        return list_dict(result)

    @classmethod
    async def get_list_view_page(cls, page: int, page_size: int,
                                 repository: Type[Repository], model: ModelType, session: AsyncSession,
                                 ) -> Dict[str, Any]:
        # Запрос с загрузкой связей и пагинацией
        skip = (page - 1) * page_size
        items, total = await repository.get_list_view_page(skip, page_size, model, session)
        items = list_dict(items)
        result = make_paginated_response(items, total, page, page_size)
        return result

    @classmethod
    async def get_list_view(cls, lang: str, repository: Type[Repository],
                            model: ModelType, session: AsyncSession, ) -> List[tuple]:
        # Запрос с загрузкой связей и без пагинации
        rows = await repository.get_list(model, session)
        list_fields = ['name']
        result = [flatten_dict_with_localized_fields(obj.to_dict_fast(), list_fields, lang) for obj in rows]
        return result

    @classmethod
    async def get_detail_view(cls, lang: str, id: int, repository: Type[Repository],
                              model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """ Получение и обработка записи по ID с автоматическим переводом недостающих локализованных полей """
        detail_fields = settings.DETAIL_VIEW
        obj = await repository.get_by_id(id, model, session)
        result = flatten_dict_with_localized_fields(inst_dict(obj), detail_fields, lang)
        return result

    @classmethod
    async def fill_index(cls, repository: Type[Repository], model: ModelType,
                         session: AsyncSession, **kwargs) -> Type[IndexFillResponse]:
        """
            УДАЛИТЬ
            заполнение/обновление поля search_content для индекса
            для заполнения индекса установить kwargs['search_content'] = None
            для обновления индекса этого ключа быть не должно
            RESPONSE_MODEL:
            model: str
            index: bool
            number_of_records: Optional[int] = 0
            number_of_indexed_records: Optional[int] = 0
        """
        try:
            logger.info(f'fill index. model={model.__name__}')
            result = IndexFillResponse(model=model.__name__)
            if not hasattr(model, 'search_content'):
                result.index = False
                result.message = f'Model "{model.__name__}" has no fts index'
                return result
            # получаем записи
            items = await repository.get_index(model, session, search_content=None)
            logger.error(f'{len(items)=} ============================================')
            # schema = get_pyschema(model, 'ReadRelation')
            data: list = []
            for item in items:
                data.append({'id': item.id,
                             'search_content': prepare_search_string(get_data_for_search(item))})
                # prepare_search_string(schema.validate(item).model_dump(mode='json'))
                # prepare_search_string(get_data_for_search(item))
                # если не работает второй вариант, применяй первый выше
            result.number_of_records = len(data)
            await repository.my_bulk_updates(data, model, session)
            result.index = True
            result.message = 'индекс успешно создан'
            logger.info(result.message)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'fill_index.error: {e}')
        # from app.core.utils.common_utils import jprint
        # jprint(data)
        # return response

    @classmethod
    async def reindex_all_searchable_models(cls, batch_size: int = 1000):
        """ заполнение Item.search_content
            УДАЛИТЬ ?  В МАЕ 2027
        """
        if _reindex_task_lock.locked():
            logger.debug("Переиндексация уже идет, запрос поставлен в очередь (проигнорирован)")
            return

        async with _reindex_task_lock:
            start_time = asyncio.get_event_loop().time()
            logger.info("--- НАЧАЛО полной переиндексации ---")
            total_updated = 0
            async with DatabaseManager.session_maker() as session:
                # 1. Находим все классы, унаследованные от SearchableMixin
                # (Или просто сканируем Base.metadata)
                searchable_models = [mapper.class_ for mapper in Base.registry.mappers if
                                     "search_content" in mapper.attrs]

                for model in searchable_models:
                    # 2. Ищем записи с пустым индексом для конкретной модели
                    stmt = (select(model.id).where(model.search_content.is_(None)).limit(batch_size))
                    result = await session.execute(stmt)
                    ids_to_update = result.scalars().all()

                    if not ids_to_update:
                        continue

                    print(f"[DEBUG] Переиндексация {model.__name__}: {len(ids_to_update)} записей")

                    # 3. Обработка батча
                    for obj_id in ids_to_update:
                        # Вызываем логику загрузки "матрешки" (нужно сделать её тоже универсальной)
                        # Если у моделей разные схемы, можно добавить метод в Mixin
                        repo: Type[Repository] = get_repo(model)
                        item = await repo.get_by_id(obj_id, model, session)
                        # item = await get_data_by_id_and_model(obj_id, model, session)
                        search_str = prepare_search_string(get_data_for_search(item))
                        await session.execute(
                            update(model).where(model.id == obj_id).values(search_content=search_str)
                        )
                    await session.commit()
                    count = len(ids_to_update)
                    if count > 0:
                        total_updated += count
                        logger.info(f"Обновлено {count} записей для модели {model.__name__}")
            end_time = asyncio.get_event_loop().time()
            duration = round(end_time - start_time, 2)

            # ФИНАЛЬНЫЙ СИГНАЛ
            logger.success(

                f"--- ЗАВЕРШЕНО: переиндексация окончена --- "
                f"Всего обновлено: {total_updated} | Время: {duration} сек."
            )

    @classmethod
    def is_dependencies(cls, model: ModelType) -> bool:
        """
              проверяет, входит ли эта модель в реестр зависимых от индексируемой модели
              и если входит - возвращает индексируемую (главную) модель
        """
        path: str = get_search_dependencies(model)
        if not path:
            return False
        res = path.split('.')[-1].capitalize()
        return res == 'Item'

    @classmethod
    async def pre_run_background_task(cls, id: int, background_tasks: BackgroundTasks,
                                      repository: Type[Repository],
                                      model: ModelType):
        """
            1. проверяет является ли модель привязанной к items, но items
            2. если да - отправляет задачу на обновление поля items.search_content
        """
        if model.__name__ == 'Item':
            return
        path: str = get_search_dependencies(model)
        logger.warning(f'background_tasks.add_task {path=}')
        if not path or path.split('.')[-1].capitalize() != 'Item':
            return
        background_tasks.add_task(
            repository.run_sync_background, start_model=model, start_id=id,
            path_str=path, session_factory=DatabaseManager.session_maker,
            skip_keys=cls.skip_keys
        )
        logger.warning("background_tasks.add_task: status: ok")

    @classmethod
    async def search_geans(cls, search: str, similarity_threshold: float,
                           page: int, page_size: int,
                           repository: Type[Repository], model: ModelType,
                           session: AsyncSession,
                           ) -> Dict[str, Any]:
        logger.warning('this is undex is not available now. Redirection to fts search')
        return await cls.search_fts(search, page, page_size, repository, model, session)

    @classmethod
    async def search_geans_all(cls, search: str,
                               repository: Type[Repository],
                               model: ModelType, session: AsyncSession, limit: int = 20) -> List[dict]:
        logger.warning('this is undex is not available now. Redirection to fts search')
        return await cls.search_fts_all(search, repository, model, session, limit)

    @classmethod
    async def get_image_by_id(self, id: int,
                              repository: Repository,
                              model: ModelType,
                              session: AsyncSession,
                              image_service: ThumbnailImageService):
        """
            получение полноразмерного изображения по id напитка
        """
        #  ПОИСК КОЛОНКИ image_id
        if not has_column(model, 'image_id'):
            raise HTTPException(status_code=422, detail=f'{model.__name__} model has no images at all')
        # 1. получение image_id by id
        image_id = await repository.get_image_id(id, model, session)
        if not image_id:
            raise HTTPException(status_code=402, detail=f'instance {model.__name__} with {id=} not found')
        # 2. получение image by image_id
        image = await image_service.get_full_image(image_id)
        return image

    @classmethod
    async def get_thumbnail_by_id(
        self, id: int, repository: Repository, model: ModelType, session: AsyncSession,
        image_service: ThumbnailImageService
    ):
        """
            получение полноразмерного изображения по id напитка
        """
        #  ПОИСК КОЛОНКИ image_id
        if not has_column(model, 'image_id'):
            raise HTTPException(status_code=422, detail=f'{model.__name__} model has no images at all')
        # 1. получение image_id by id
        image_id = await repository.get_image_id(id, model, session)
        if not image_id:
            raise HTTPException(status_code=402, detail=f'instance {model.__name__} with {id=} not found')
        # 2. получение thumbnail by image_id
        image = await image_service.get_thumbnail(image_id)
        return image

    @classmethod
    async def search_fts(cls, search: str,
                         page: int, page_size: int,
                         repository: Type[Repository], model: ModelType,
                         session: AsyncSession,
                         ) -> Dict[str, Any]:
        try:
            # Запрос с загрузкой связей и пагинацией
            skip = (page - 1) * page_size
            if not search:
                items, total = await repository.get_full_with_pagination(skip, page_size, model, session)
                items = list_dict(items)
                return make_paginated_response(items, total, page, page_size)
            # определаяем тип поиска (geans OR b-tree
            if hasattr(model, 'search_content'):
                if formatted_search := formatted_query(search):
                    items, total = await repository.search_fts(formatted_search, skip, page_size, model, session)
                else:
                    items, total = await repository.search(search, skip, page_size, model, session)
            else:
                # model is not indexed by GIN
                items, total = await repository.search(search, skip, page_size, model, session)
            items = list_dict(items)
            result: dict = make_paginated_response(items, total, page, page_size)
            return result
        except Exception as e:
            logger.error(f'search_geans.error: {e}')
            raise HTTPException(status_code=501, detail=f'{e}')

    @classmethod
    async def search_fts_all(cls, search: str,
                             repository: Type[Repository],
                             model: ModelType, session: AsyncSession,
                             limit: int = 20) -> List[dict]:
        try:
            # Запрос с загрузкой связей без пагинации
            # определаяем тип поиска (tfs OR b-tree
            if not search:
                response = await repository.get_full(model, session, limit)
                return list_dict(response)
            if hasattr(model, 'search_content'):
                if formatted_search := formatted_query(search):
                    items = await repository.search_fts_all(formatted_search, model, session, limit)
                else:
                    items = await repository.search_all(search, model, session, limit)
            else:
                # model is not indexed by GIN
                items = await repository.search_all(search, model, session)
            return list_dict(items)
        except Exception as e:
            logger.error(f'search_geans_all.error: {e}')
            raise HTTPException(status_code=501, detail=f'{e}')

    @classmethod
    async def clicksearch(cls, search: str, mode: str,
                          page: int, page_size: int,
                          repository: Type[Repository], model: ModelType,
                          session: AsyncSession,
                          ch_client, table: str = 'items_search'):
        """ поиск searh thru click - УДАЛИТЬ ПОТОМ ПОКА ПОИСК ПО CLICK SEARCH неподошел"""
        # 0. запрос в clickhouse
        click_service = FullTextSearch
        click: tuple = await click_service.search(search, table, ch_client, mode)
        if click:
            total = len(click)
            ids = click[(page - 1) * page_size:page * page_size]
            response = await repository.get_by_ids(ids, model, session)
            result = make_paging_dict(response, page, page_size, total)
            return result
        else:
            return []

    @classmethod
    async def run_reindex_worker(cls, session_factory, force_all: bool = False):
        if _REINDEX_LOCK.locked():
            logger.info("Воркер уже запущен, пропускаю...")
            return
        Item = get_model_by_name('Item')
        async with _REINDEX_LOCK:
            logger.info("Запуск массовой переиндексации...")

            # Определяем критерии устаревания (2 года)
            # two_years_ago = datetime.now(timezone.utc) - timedelta(days=730)
            # Item = get_model_by_name('Item')

            async with session_factory() as session:
                # 1. Строим фильтр
                filters = []
                if not force_all:
                    filters.append(
                        or_(
                            Item.search_content.is_(None),
                            # Item.search_content == "",
                            # Item.updated_at < two_years_ago
                        )
                    )

                # 2. Считаем общий объем работы
                count_stmt = select(func.count()).select_from(Item)
                if filters:
                    count_stmt = count_stmt.where(*filters)
                total_to_process = await session.scalar(count_stmt)

                logger.info(f"Найдено {total_to_process} записей для обработки")

                # 3. Пакетная обработка
                processed = 0
                while processed < total_to_process:
                    # Загружаем пачку Item вместе с Drink (важно для скорости!)
                    stmt = (select(Item).options(selectinload(Item.drink)).limit(cls.BATCH_SIZE).order_by(Item.id)
                            # Стабильная сортировка для смещения
                            )
                    if filters:
                        stmt = stmt.where(*filters)

                    result = await session.execute(stmt)
                    items = result.scalars().all()

                    if not items:
                        break

                    # Обрабатываем пачку
                    for item in items:
                        if item.drink:
                            # Используем вашу логику парсинга
                            drink_dict = item.drink.to_dict()
                            content = extract_text_ultra_fast(drink_dict, cls.skip_keys)
                            item.search_content = content.lower()

                    # Фиксируем пачку в БД
                    await session.commit()
                    processed += len(items)
                    logger.info(f"Прогресс: {processed}/{total_to_process}")

                    # Короткая пауза, чтобы дать event loop подышать
                    await asyncio.sleep(0.1)

            logger.info("Массовая переиндексация завершена успешно")

    @classmethod
    async def search_by_hash_cursor(query: str, model: ModelType, repo: Type[Repository],
                                    session: AsyncSession, cursor: dict = None, limit: int = 15):
        """
            поиск по хэш индексу с паниеацией
        """
        if not hasattr(model, 'word_hashes'):
            raise HTTPException(status_code=502, detail='this model has no hash index')
        # 1. Нормализация
        tokens = tokenize(query)
        if not tokens:
            return {"items": [], "total": 0}

        # 2. Сбор всех целевых хешей (включая префиксы последнего слова)
        main_hashes = [get_cached_hash(t) for t in tokens]
        prefix_hashes = await repo.get_hashes_by_prefix(session, tokens[-1])
        all_hashes = list(set(main_hashes) | set(prefix_hashes))

        # 3. Метаданные (Частоты и Total)
        # В идеале: закэшировать word_weights в Redis на 5 минут по ключу MD5(query)
        word_freqs, total_count = await repo.get_search_metadata(session, all_hashes)

        boost = 15.0
        word_weights = {h: (1.0 / math.log(freq + 1.5)) * boost for h, freq in word_freqs.items()}

        # 4. Поиск данных
        last_score = cursor.get("score") if cursor else None
        last_id = cursor.get("id") if cursor else None

        results = await repo.find_items_hybrid(
            session, word_weights, last_score, last_id, limit
        )

        # 5. Формирование ответа
        items_out = []
        for row in results:
            # Превращаем Row в dict, учитывая структуру (Item, score)
            item_dict = {column.name: getattr(row.Item, column.name) for column in row.Item.__table__.columns}
            item_dict["score"] = round(float(row.score), 4)
            items_out.append(item_dict)

        # Определяем следующий курсор
        next_cursor = None
        if len(items_out) == limit:
            next_cursor = {"score": items_out[-1]["score"], "id": items_out[-1]["id"]}

        return {"total_found": total_count, "items": items_out, "next_cursor": next_cursor,
                "has_more": next_cursor is not None}
