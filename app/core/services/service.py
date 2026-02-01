# app.core.service/service.py
import asyncio
from abc import ABCMeta
from datetime import datetime
from fastapi import HTTPException, BackgroundTasks
from typing import List, Optional, Tuple, Type
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import DatabaseManager
from app.core.config.project_config import settings
from app.core.models.base_model import Base, get_model_by_name
from app.core.repositories.sqlalchemy_repository import ModelType, Repository
# from app.core.utils.alchemy_utils import get_models
from app.core.utils.common_utils import flatten_dict_with_localized_fields
from app.core.utils.pydantic_utils import make_paginated_response, prepare_search_string, get_data_for_search, get_repo
from app.service_registry import register_service, get_search_dependencies
from app.core.schemas.base import IndexFillResponse

joint = '. '
_REINDEX_LOCK = asyncio.Lock()

_reindex_task_lock = asyncio.Lock()


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
    #  get_or_create, update_or_create
    default: list = ['name']

    @classmethod
    async def create(cls, data: ModelType, repository: Type[Repository], model: ModelType,
                     session: AsyncSession, **kwargs) -> ModelType:
        """ create & return record """
        # удаляет пустые поля
        data_dict = data.model_dump(exclude_unset=True)
        obj = model(**data_dict)
        result = await repository.create(obj, model, session)
        await session.commit()
        return result

    @classmethod
    async def get_or_create(cls, data: ModelType, repository: Type[Repository],
                            model: ModelType, session: AsyncSession,
                            default: List[str] = None, **kwargs) -> Tuple[ModelType, bool]:
        """
            находит или создaет запись
            возвращает instance и True (запись создана) или False (запись существует)
        """
        try:
            if default is None:
                default = cls.default
            data_dict = data.model_dump(exclude_unset=True)
            default_dict = {key: val for key, val in data_dict.items() if key in default}
            # ошибка НУЖЕН ПОИСК ПО УНИКАЛЬНЫМ И СВЯЗАННЫМ ПОЛЯМ
            # поиск существующей записи по совпадению объектов по уникальным полям
            instance = await repository.get_by_fields(default_dict, model, session)
            if instance:
                return instance, False
            # запись не найдена
            obj = model(**data_dict)
            instance = await repository.create(obj, model, session)
            await session.commit()
            return instance, True
        except IntegrityError as e:
            await session.rollback()
            raise Exception(f'Integrity error: {e}')
        except Exception as e:
            await session.rollback()
            raise Exception(f"UNKNOWN_ERROR: {str(e)}") from e

    @classmethod
    async def update_or_create(cls, id: int, data: ModelType, repository: Type[Repository],
                               model: ModelType, session: AsyncSession,
                               default: List[str] = None, **kwargs) -> Tuple[ModelType, bool]:
        """
            находит и обновляет запись или создает если ее нет
        """
        try:
            if default is None:
                default = cls.default
            data_dict = data.model_dump(exclude_unset=True)
            default_dict = {key: val for key, val in data_dict.items() if key in default}
            # поиск существующей записи по совпадению объектов по уникальным полям
            instance = await repository.get_by_fields(default_dict, model, session)
            if instance:
                # запись найдена, обновляем
                result = await repository.patch(instance, data_dict, session)
                await session.commit()
                return result['data'], False
            # запись не найдена
            obj = model(**data_dict)
            instance = await repository.create(obj, model, session)
            await session.commit()
            return instance, True
        except IntegrityError as e:
            await session.rollback()
            raise Exception(f'Integrity error: {e}')
        except Exception as e:
            await session.rollback()
            raise Exception(f"UNKNOWN_ERROR: {str(e)}") from e

    @classmethod
    async def create_relation(cls, data: ModelType,
                              repository: Type[Repository], model: ModelType, session: AsyncSession,
                              **kwargs) -> ModelType:
        """
        создание записей из json - со связями
        """

        data_dict = data.model_dump(exclude_unset=True)
        result = await repository.get_by_obj(data_dict, model, session)
        if result:
            return result
        else:
            obj = model(**data_dict)

            result = await repository.create(obj, model, session)
            await session.commit()
            # тут можно добавить преобразования результата потом commit в роутере
            return result

    @classmethod
    async def get_all(cls, ater_date: datetime,
                      page: int, page_size: int, repository: Type[Repository], model: ModelType,
                      session: AsyncSession) -> List[dict]:
        # Запрос с загрузкой связей и пагинацией
        skip = (page - 1) * page_size
        items, total = await repository.get_all(ater_date, skip, page_size, model, session)
        """
            result = {"items": items,
                  "total": total,
                  "page": page,
                  "page_size": page_size,
                  "has_next": skip + len(items) < total,
                  "has_prev": page > 1}
        """
        result = make_paginated_response(items, total, page, page_size)
        return result

    @classmethod
    async def get(cls, after_date: datetime,
                  repository: Type[Repository], model: ModelType,
                  session: AsyncSession) -> Optional[List[ModelType]]:
        # Запрос с загрузкой связей -  возвращает список
        result = await repository.get(after_date, model, session)
        return result

    @classmethod
    async def get_by_id(
            cls, id: int, repository: Type[Repository],
            model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """Получение записи по ID с автоматическим переводом недостающих локализованных полей"""
        result = await repository.get_by_id(id, model, session)
        return result

    @classmethod
    async def patch(cls, id: int, data: ModelType,
                    repository: Type[Repository],
                    model: ModelType,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession) -> dict:
        """
        Редактирование записи по ID
        Возвращает dict с результатом операции
        """

        # Получаем существующую запись
        existing_item = await repository.get_by_id(id, model, session)
        if not existing_item:
            return {'success': False, 'message': f'Редактируемая запись {id} не найдена на сервере',
                    'error_type': 'not_found'}
        data_dict = data.model_dump(exclude_unset=True)

        if not data_dict:
            return {'success': False, 'message': 'Нет данных для обновления', 'error_type': 'no_data'}
        # Выполняем обновление
        result = await repository.patch(existing_item, data_dict, session)
        if result.get('success'):
            await cls.invalidate_search_index(id, repository, model, session)
            await session.commit()
            background_tasks.add_task(cls.run_reindex_worker, model.__name__, DatabaseManager.session_maker)
        else:
            await session.rollback()
        # Обрабатываем результат
        if isinstance(result, dict):
            if result.get('success'):
                await cls.invalidate_search_index(id, repository, model, session)
                session.commit()
                background_tasks.add_task(cls.run_reindex_worker, model.__name__, DatabaseManager.session_maker)
                return {'success': True, 'data': result.get('data'), 'message': f'Запись {id} успешно обновлена'}
            else:
                error_type = result.get('error_type')
                message = result.get('message', 'Неизвестная ошибка')
                field_info = result.get('field_info')

                if error_type == 'unique_constraint_violation':
                    return {'success': False, 'message': message,
                            'error_type': 'unique_constraint_violation', 'field_info': field_info}
                elif error_type == 'foreign_key_violation':
                    return {'success': False, 'message': message,
                            'error_type': 'foreign_key_violation', 'field_info': field_info}
                elif error_type == 'update_failed':
                    return {'success': False, 'message': message,
                            'error_type': 'update_failed'}
                elif error_type == 'integrity_error':
                    return {'success': False, 'message': message,
                            'error_type': 'integrity_error', 'field_info': field_info}
                elif error_type == 'database_error':
                    return {'success': False, 'message': message,
                            'error_type': 'database_error'}
                else:
                    return {'success': False, 'message': message,
                            'error_type': error_type}
        else:
            return {'success': False, 'message': f'Неизвестная ошибка при обновлении записи {id}',
                    'error_type': 'unknown_error'}

    @classmethod
    async def delete(cls, id: int, model: ModelType, repository: Type[Repository],
                     background_tasks: BackgroundTasks,
                     session: AsyncSession) -> bool:
        instance = await repository.get_by_id(id, model, session)
        if instance is None:
            raise ValueError(f'instanse with {id=} not found')
        try:
            await repository.delete(instance, session)
            await session.flush()
            await cls.invalidate_search_index(id, repository, model, session)
            await session.commit()
            background_tasks.add_task(cls.run_reindex_worker, model.__name__, DatabaseManager.session_maker)
        except IntegrityError:
            await session.rollback()  # Откат при конфликте связей
            raise PermissionError(f"Cannot delete record {id} of {model.__name__}: related data exists")
        except Exception as e:
            await session.rollback()
            raise Exception(f'{model.__name__}, {id}, {e}')

    @classmethod
    async def search(cls,
                     repository: Type[Repository],
                     model: ModelType,
                     session: AsyncSession,
                     **kwargs) -> List[ModelType]:
        """
            базовый поиск
        """
        paging = False
        if not kwargs:
            kwargs: dict = {}
        else:
            if kwargs.get('page') and kwargs.get('page_size'):
                limit = kwargs.pop('page_size')
                skip = (kwargs.pop('page') - 1) * limit
                kwargs['limit'], kwargs['skip'] = limit, skip
                paging = True
        if paging:
            items, total = await repository.search(model, session, **kwargs)
            result = {"items": items,
                      "total": total,
                      "page": skip,
                      "page_size": limit,
                      "has_next": skip + len(items) < total,
                      "has_prev": skip > 1}
        else:
            result = await repository.search_all(model, session, **kwargs)
        return result

    @classmethod
    async def search_all(cls,
                         search_str: str,
                         repository: Type[Repository],
                         model: ModelType,
                         session: AsyncSession,
                         **kwargs) -> List[ModelType]:
        """
            базовый поиск без пагинации
        """
        kwargs = {'search_str': search_str}
        result = await repository.search_all(model, session, **kwargs)
        return result

    @classmethod
    async def get_list_view_page(cls, page: int, page_size: int,
                                 repository: Type[Repository], model: ModelType, session: AsyncSession, ) -> List[dict]:
        # Запрос с загрузкой связей и пагинацией
        skip = (page - 1) * page_size
        rows, total = await repository.get_list_view_page(skip, page_size, model, session)
        result = {"rows": rows,
                  "total": total,
                  "page": page,
                  "page_size": page_size,
                  "has_next": skip + len(rows) < total,
                  "has_prev": page > 1}
        return result

    @classmethod
    async def get_list_view(cls, lang: str, repository: Type[Repository],
                            model: ModelType, session: AsyncSession, ) -> List[tuple]:
        # Запрос с загрузкой связей и без пагинацией
        rows = await repository.get_list(model, session)
        list_fields = ['name']
        result = [flatten_dict_with_localized_fields(obj.to_dict(), list_fields, lang) for obj in rows]
        return result

    @classmethod
    async def get_detail_view(cls, lang: str, id: int, repository: Type[Repository],
                              model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """ Получение и обработка записи по ID с автоматическим переводом недостающих локализованных полей """
        detail_fields = settings.DETAIL_VIEW
        obj = await repository.get_by_id(id, model, session)
        # return obj
        if not obj:
            return None
        result = flatten_dict_with_localized_fields(obj.to_dict(), detail_fields, lang)
        return result

    @classmethod
    async def fill_index(cls, repository: Type[Repository], model: ModelType,
                         session: AsyncSession, **kwargs) -> Type[IndexFillResponse]:
        """
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
            result = IndexFillResponse(model=model.__name__)
            if not hasattr(model, 'search_content'):
                result.index = False
                result.message = f'Model "{model.__name__}" has no trigramm index'
                return result
            # получаем записи
            items = await repository.get_index(model, session, search_content=None)
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
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'fill_index.error: {e}')
        # from app.core.utils.common_utils import jprint
        # jprint(data)
        # return response

    @classmethod
    async def reindex_all_searchable_models(cls, batch_size: int = 1000):
        """ заполнение Item.search_content
            УДАЛИТЬ ?
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
                    stmt = (select(model.id).where(model.search_content == None).limit(batch_size))
                    result = await session.execute(stmt)
                    ids_to_update = result.scalars().all()

                    if not ids_to_update:
                        continue

                    print(f"[DEBUG] Переиндексация {model.__name__}: {len(ids_to_update)} записей")

                    # 3. Обработка батча
                    for obj_id in ids_to_update:
                        # Вызываем твою логику загрузки "матрешки" (нужно сделать её тоже универсальной)
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
    async def invalidate_search_index(cls, id: int, repository: Type[Repository],
                                      model: ModelType, session: AsyncSession, **kwargs):
        """
        сбрасывает значение поля search_content основной таблиы в случае изменений в зависимых таблицах
        это часть стратегии поиска
        """
        if not cls.is_dependencies(model):
            logger.info(f'{model.__name__} has no relationships with Items')
            return
        try:
            item = get_model_by_name('Item')
            await repository.invalidate_search_index(id, item, model, session)
        except Exception as e:
            logger.error(f'{model.__name__} invalidate_search_index error: {e}')

    @classmethod
    async def run_reindex_worker(cls, model_name: str, session_factory):
        if _REINDEX_LOCK.locked():
            return  # Уже работает, новый запуск не нужен

        async with _REINDEX_LOCK:
            # Небольшая пауза (дебаунс), чтобы подождать,
            # если идет серия мелких правок в справочниках
            model = get_model_by_name(model_name)
            if cls.is_dependencies(model):
                await asyncio.sleep(2)
                async with session_factory() as new_session:
                    repository = get_repo(model)
                    logger.info("Авто-подметатель: обнаружены пустые индексы, начинаю сборку...")
                    await cls.fill_index(repository, model, new_session)
