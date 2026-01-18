# app.core.service/service.py
from abc import ABCMeta
from datetime import datetime
from typing import List, Optional, Tuple, Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import Session

from app.core.config.project_config import settings
from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.core.utils.alchemy_utils import get_models
from app.core.utils.common_utils import flatten_dict_with_localized_fields
from app.core.utils.pydantic_utils import make_paginated_response
from app.service_registry import register_service

joint = '. '


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
    def get_model_by_name(cls, name: str) -> ModelType:
        for mode in get_models():
            if any((mode.__name__.lower() == name, mode.__tablename__.lower() == name)):
                return mode

    @classmethod
    async def create(cls, data: ModelType, repository: Type[Repository], model: ModelType,
                     session: AsyncSession) -> ModelType:
        """ create & return record """
        # удаляет пустые поля
        data_dict = data.model_dump(exclude_unset=True)
        obj = model(**data_dict)
        result = await repository.create(obj, model, session)
        return result

    @classmethod
    async def get_or_create(cls, data: ModelType, repository: Type[Repository],
                            model: ModelType, session: AsyncSession,
                            default: List[str] = None) -> Tuple[ModelType, bool]:
        """
            находит или создет запись
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
            await session.flush()
            await session.refresh(instance)
            return instance, True
        except IntegrityError as e:
            raise Exception(f'Integrity error: {e}')
        except Exception as e:
            raise Exception(f"UNKNOWN_ERROR: {str(e)}") from e

    @classmethod
    async def update_or_create(cls, id: int, data: ModelType, repository: Type[Repository],
                               model: ModelType, session: AsyncSession,
                               default: List[str] = None) -> Tuple[ModelType, bool]:
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
                return result, False
            # запись не найдена
            obj = model(**data_dict)
            instance = await repository.create(obj, model, session)
            await session.flush()
            await session.refresh(instance)
            return instance, True
        except IntegrityError as e:
            raise Exception(f'Integrity error: {e}')
        except Exception as e:
            raise Exception(f"UNKNOWN_ERROR: {str(e)}") from e

    @classmethod
    async def create_relation(cls, data: ModelType,
                              repository: Type[Repository], model: ModelType, session: AsyncSession) -> ModelType:
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
            # тут можно добавить преобразования результата потом commit в роутере
            return result

    @classmethod
    async def get_all(cls, ater_date: datetime,
                      page: int, page_size: int, repository: Type[Repository], model: ModelType,
                      session: AsyncSession ) -> List[dict]:
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
                  session: AsyncSession,) -> Optional[List[ModelType]]:
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
                    model: ModelType, session: AsyncSession) -> dict:
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
        # Обрабатываем результат
        if isinstance(result, dict):
            if result.get('success'):
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
                     session: AsyncSession) -> bool:
        instance = await repository.get_by_id(id, model, session)
        if instance:
            result = await repository.delete(instance, session)

            if result == "foreign_key_violation":
                return {'success': False, 'deleted_count': 0,
                        'message': 'Невозможно удалить запись: на неё ссылаются другие объекты'}
            elif isinstance(result, str) and result.startswith(('integrity_error:', 'database_error:')):
                return {'success': False, 'deleted_count': 0,
                        'message': f'Ошибка базы данных при удалении: {result.split(":", 1)[1]}'}
            elif result is True:
                return {'success': True, 'deleted_count': 1, 'message': f'Запись {id} удалена'}
            else:
                return {'success': False, 'deleted_count': 0, 'message': f'Запись {id} обнаружена, но не удалена.'}
        else:
            return {'success': False, 'deleted_count': 0, 'message': f'Запись {id} не найдена'}

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
