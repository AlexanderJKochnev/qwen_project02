# app/core/repositories/sqlalchemy_repository.py
"""
    переделать на ._mapping (.mappings().all()) (в результате словарь вместо объекта)
    get_all     result.mappings().all()
    get_by_id   result.scalar_one_or_none()
"""
from abc import ABCMeta
from datetime import datetime
from re import search as research
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from loguru import logger
from sqlalchemy import (and_, cast, desc, func, insert, inspect, literal, or_, Row, RowMapping, select, Select, Text,
                        text, update)
from sqlalchemy.dialects import postgresql  # NOQA: F401
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, load_only

from app.core.config.project_config import settings
from app.core.exceptions import AppBaseException
from app.core.models.base_model import get_model_by_name, plural
from app.core.repositories.repo_background_tasks import Background
from app.core.types import ModelType
# from sqlalchemy.sql.elements import ColumnElement
from app.core.utils.alchemy_utils import (create_enum_conditions, create_search_conditions2, get_field_list,
                                          get_sql_search)
from app.core.utils.reindexation import extract_text_ultra_fast
from app.service_registry import get_child, register_repo

# длина списка поисковой выдачи
search_site = min(settings.PAGE_DEFAULT, 20)


class RepositoryMeta(ABCMeta):

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        # Регистрируем сам класс, а не его экземпляр
        if not attrs.get('__abstract__', False):
            key = name.lower().replace('repository', '')
            register_repo(key, new_class)
            # cls._registry[key] = new_class  # ← Сохраняем класс!
        return new_class


class Repository(Background, metaclass=RepositoryMeta):
    __abstract__ = True
    model: ModelType

    @staticmethod
    def get_related_model(model: ModelType):
        """
            получение связанной модели
        """
        related_model_name = get_child(model)
        if not related_model_name:
            return None
        child_model_name: str = get_child(model)
        if not child_model_name:
            return None
        return get_model_by_name(child_model_name.capitalize())

    @classmethod
    async def get_count(cls, query: Select, session: AsyncSession):
        """ ПОДСЧЕТ ОБЩЕГО КОЛ-ВА ЗАПИСЕЙ В СЛОЖНЫХ ЗАПРОСАХ (С ФИЛЬТРАМИ)"""
        return (await session.execute(
                select(func.count()).select_from(query.subquery())
                )).scalar()

    @classmethod
    def get_query(cls, model: ModelType) -> Select:
        """
            Переопределяемый метод.
            Возвращает select() с полными selectinload.
            По умолчанию — без связей.
        """
        return select(model)

    @classmethod
    def get_short_query(cls, model: ModelType, fields: tuple = ('id', 'name')):
        """
            Возвращает список модели только с нужными полями остальные None
            - использовать для list_view и вообще где только можно.
            для моделей с зависимостями - переопределить
        """
        fields = get_field_list(model, starts=fields)
        return select(model).options(load_only(*fields))

    @classmethod
    async def pagination(cls, stmt: Select, skip: int, limit: int, session: AsyncSession):
        """
            получает запрос, сдвиг и размер страницы, сессию
            возвращает список instances и кол-во записей
        """
        # count_stmt = select(func.count()).select_from(stmt)
        # total = await session.scalar(count_stmt) or 0
        total = await cls.get_count(stmt, session)
        if total == 0:
            return None, total
        stmt = stmt.offset(skip).limit(limit)
        # compiled_pg = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items, total

    @classmethod
    async def nonpagination(cls, stmt: Select, session: AsyncSession) -> List[ModelType]:
        """
            получает запрос
            возвращает список instances
        """
        result = await session.execute(stmt)
        if result:
            items = result.scalars().all()
            return items
        else:
            return None

    @classmethod
    async def get_match(cls, model: ModelType, relevance, search: str,
                        session: AsyncSession,
                        skip: Union[int, None] = None,
                        limit: Union[int, None] = None) -> list:
        """
            получение ранжированного списка по поиску search_content
            если есть пагинация - только для заданной страницы
        """
        stmt = (select(model.id, relevance)
                .where(cast(literal(search), Text).op("<%")(model.search_content))
                .order_by(desc(text("rank"))))
        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)
        response = await session.execute(stmt)
        matching_ids = [row[0] for row in response.fetchall()]
        # logger.warning(f'{len(matching_ids)=}')
        return matching_ids

    @classmethod
    async def get_greenlet(cls, model: ModelType, matching: List, session: AsyncSession) -> List[ModelType]:
        """
            загрузка связей по списку ids,
            возвращает ранжированный список instances
        """
        stmt = cls.get_query(model).where(model.id.in_(matching))
        result = await session.execute(stmt)
        items = result.scalars().all()
        items_map = {item.id: item for item in items}
        if matching:
            items = [items_map[id_] for id_ in matching if id_ in items_map]
        return items

    @classmethod
    async def invalidate_search_index(cls, id: int, item: ModelType, model: ModelType, session: AsyncSession):
        """
            УДАЛИТЬ 23 АПРЕЛЯ
            обнуление item.search_content в записях у которых child records updated
        """
        try:
            stmp = update(item).where(cls.item_exists(id)).values({'search_content': None})
            # Компилируем специально для PostgreSQL
            # from sqlalchemy.dialects import postgresql
            # compiled = stmp.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            await session.execute(stmp)
        except Exception as e:
            raise Exception(f'fault of invalidate_search_index. {e}')

    @classmethod
    async def invalidate_parent_search_content(cls, start_id, current_model, path_str, session):
        """
        НЕ ИСПОЛЬЗУЕТСЯ !!! УДАЛИТЬ !!!
        Обновляет search_content у корневой модели (Item),
        основываясь на изменениях в дочерней модели (например, Category).
        """
        logger.warning(f'invalidate_parent_search_content {path_str}')
        # 1. Строим подзапрос для поиска нужных ID корневой модели
        # Начинаем от текущей измененной записи (например, Category)
        subq_stmt = select(current_model.id).where(current_model.id == start_id)

        path_parts = path_str.split('.')
        last_model = current_model

        for target_part in path_parts:
            mapper = inspect(last_model)
            target_rel_key = None

            for rel in mapper.relationships:
                if rel.mapper.class_.__name__.lower() == target_part.lower():
                    target_rel_key = rel.key
                    last_model = rel.mapper.class_
                    break

            if not target_rel_key:
                raise AttributeError(f"Связь '{target_part}' не найдена в {last_model.__name__}")

            # Джоиним следующую модель в цепочке
            subq_stmt = subq_stmt.join(getattr(mapper.class_, target_rel_key))

        # Теперь last_model — это Item. Выбираем только его ID.
        # .scalar_subquery() превращает это в подзапрос для WHERE IN (...)
        target_ids_subq = subq_stmt.with_only_columns(last_model.id).distinct().scalar_subquery()

        # 2. Формируем финальный UPDATE запрос
        stmt = (update(last_model).where(last_model.id.in_(target_ids_subq)).values({'search_content': None}))

        # 3. Выполняем
        result = await session.execute(stmt)
        updated_count = result.rowcount
        logger.warning(f'очищено {updated_count}')

    @classmethod
    async def get_root_ids_by_path(cls, current_model, start_id: int, path_str: str, session: AsyncSession):
        """
        current_model: Модель, где произошло изменение (например, Category)
        start_id: ID измененной записи (например, Category.id)
        path_str: Строка связи до корня (например, "subcategory.drink.item")
        """
        # Начинаем с модели, в которой находимся (Category)
        stmt = select(current_model).where(current_model.id == start_id)

        # Итерируемся по пути
        path_parts = path_str.split('.')
        last_model = current_model

        for target_part in path_parts:
            mapper = inspect(last_model)
            target_rel_key = None

            # Ищем связь (relationship) в текущей модели, которая ведет к следующей модели в пути
            for rel in mapper.relationships:
                # Сравниваем имя класса целевой модели с частью пути (регистронезависимо)
                if rel.mapper.class_.__name__.lower() == target_part.lower():
                    target_rel_key = rel.key
                    last_model = rel.mapper.class_  # Теперь это наша "текущая" модель для следующего шага
                    break

            if not target_rel_key:
                raise AttributeError(f"Связь к '{target_part}' не найдена в модели '{last_model.__name__}'")

            # Присоединяем следующую таблицу в цепочке
            stmt = stmt.join(getattr(mapper.class_, target_rel_key))

        # ВАЖНО: В конце мы выбираем ID самой последней модели в цепочке (нашего "корня")
        # last_model теперь ссылается на Item
        final_stmt = stmt.with_only_columns(last_model.id).distinct()

        return await session.scalars(final_stmt).all()

    @classmethod
    async def create(cls, obj: ModelType, model: ModelType, session: AsyncSession) -> ModelType:
        """ создание записи """
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    @classmethod
    async def bulk_create(cls, data: List[Dict], model: ModelType,
                          session: AsyncSession) -> List[ModelType] | None:
        """ быстрое массовое добавление записей из словаре may be not work
            data = [
                {"email": "user1@example.com", "username": "user1", "status": "active"},
                {"email": "user2@example.com", "username": "user2", "status": "pending"},
                {"email": "user3@example.com", "username": "user3", "status": "active"},
            ]
        """
        if not data:
            return
        stmt = insert(model).returning(model)
        result = await session.scalars(stmt, data)
        return result.all()

    @classmethod
    async def bulk_update(cls, data: List[Dict], model: ModelType,
                          session: AsyncSession) -> bool:
        """ быстрое массовое обновление записей из словарей
            data должны содержать id
            data = [
                    {'id': 104, 'seaweed_fids': ('20,cf5fefa821', '16,d0e133a318')},
                    {'id': 105, 'seaweed_fids': ('17,d1a8908ae6', '20,d2ad06361d')},
                    {'id': 106, 'seaweed_fids': ('21,d3f0b578f7', '20,d4cbc210a8')},
                    ]
        """
        # 1. получить редактируемые записи одним запросом
        data_dict: dict = {item.pop('id'): item for item in data}
        ids = list(data_dict.keys())
        instances = await cls.get_by_ids(ids, model, session)
        for instance in instances:
            datax = data_dict.get(instance.id)
            for item in datax:
                for k, v in item.items():
                    if hasattr(instance, k):
                        setattr(instance, k, v)
        await session.flush()

    @classmethod
    async def patch(cls, obj: ModelType,
                    data: Dict[str, Any], session: AsyncSession) -> Union[ModelType, dict, None]:
        """
        редактирование записи
        :param obj: редактируемая запись
        :param data: изменения в редактируемую запись
        """
        try:
            # Store original values for comparison later
            for k, v in data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            await session.flush()
            # await session.refresh(data) - не надо - дает ошибки
            return {"success": True, "data": obj}
        except IntegrityError as e:
            raise AppBaseException(message=str(e.orig), status_code=404)
        except Exception as e:
            raise AppBaseException(message=str(e), status_code=405)

    @classmethod
    def _extract_field_info_from_error(cls, error_message: str) -> dict:
        """
        Extract field name and value information from database error message
        """
        # This is a simplified version - in real implementation you might want to parse
        # specific patterns from different database error messages
        field_info = {}
        # Example parsing for PostgreSQL unique constraint violations
        if 'duplicate key value violates unique constraint' in error_message.lower():
            # Extract table and field names
            table_match = research(r'"([^"]+)"', error_message)
            if table_match:
                field_info['table'] = table_match.group(1)

            # Extract the duplicate value
            value_match = research(r'\(([^)]+)\)=\(([^)]+)\)', error_message)
            if value_match:
                field_info['field'] = value_match.group(1)
                field_info['value'] = value_match.group(2)

        elif 'foreign key constraint' in error_message.lower():
            # Extract referenced table and key info
            import re
            ref_match = re.search(r'reference "(.+?)"', error_message)
            if ref_match:
                field_info['referenced_table'] = ref_match.group(1)

        return field_info

    @classmethod
    async def delete(cls, obj: ModelType, session: AsyncSession) -> bool:
        """
        удаление записи
        :param obj: instance
        """
        # async with session.begin_nested():
        await session.delete(obj)
        # await session.expunge(obj)
        # можно отвязать и вернуть удаленный объект и проделать с ним вские штуки - например записать заново с новым ID
        return True  # , None  # , obj

    @classmethod
    async def get_by_id(cls, id: int, model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """
            get one record by id
        """
        logger.warning(f'{cls.get_related_model(model)=}')
        stmt = cls.get_query(model).where(model.id == id)
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()
        return obj

    @classmethod
    async def get_by_ids(cls, ids: Tuple[int], model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """
            get records by ids tuple
        """
        stmt = cls.get_query(model).where(model.id.in_(ids)).order_by(model.id.asc())
        # from sqlalchemy.dialects import postgresql
        # compiled_pg = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        # logger.error(compiled_pg)
        result = await cls.nonpagination(stmt, session)
        return result

    @classmethod
    async def get_by_obj(cls, data: dict, model: Type[ModelType], session: AsyncSession) -> Optional[ModelType]:
        """
        получение instance ло совпадению данных данным
        :param data:
        :type data:
        :param model:
        :type model:
        :param session:
        :type session:
        :return:
        :rtype:
        """
        valid_fields = {key: value for key, value in data.items()
                        if hasattr(model, key)}
        if not valid_fields:
            return None
        stmt = select(model).filter_by(**valid_fields)
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        return item

    @classmethod
    async def get(cls, after_date: datetime, skip: int,
                  limit: int, model: ModelType, session: AsyncSession,
                  ) -> tuple:
        """
            Запрос с загрузкой связей и пагинацией
            return Tuple[List[instances], int]
        """
        stmt = cls.get_query(model)
        if hasattr(model, 'updated_at'):
            stmt = stmt.where(model.updated_at > after_date)
        stmt = stmt.order_by(model.id.asc())
        # stmt = (cls.get_query(model).where(model.updated_at > after_date)
        #         .order_by(model.id.asc()))
        result = await cls.pagination(stmt, skip, limit, session)
        return result

    @classmethod
    async def get_all(cls, after_date: datetime, model: ModelType, session: AsyncSession,
                      limit: int = 20) -> list:
        """
            Запрос с загрузкой связей NO PAGINATION
            return List[instance]
        """
        # stmt = cls.get_query(model).where(model.updated_at > after_date).order_by(model.id.asc())
        stmt = cls.get_query(model)
        if hasattr(model, 'updated_at'):
            stmt = stmt.where(model.updated_at > after_date)
        stmt = stmt.order_by(model.id.asc())
        if limit:
            stmt = stmt.limit(limit)
        result = await cls.nonpagination(stmt, session)
        return result

    @classmethod
    async def get_by_field(cls, field_name: str, field_value: Any, model: ModelType,
                           session: AsyncSession, **kwargs):
        """
            поиск по одному полю. поисковый запрос входит в значение поля
            get_by_fields
        """
        try:
            column = getattr(model, field_name)
            if kwargs.get('equa') == 'icontains':
                stmt = select(model).where(column.icontains(field_value))
            else:
                stmt = select(model).where(column == field_value)
            if orderby := kwargs.get('order_by'):
                if kwargs.get('asc', False):
                    stmt = stmt.order_by(orderby)
                else:
                    stmt = stmt.order_by(desc(orderby))
            stmt = stmt.limit(1)
            # stmt = select(model).where(getattr(model, field_name) == field_value)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise AppBaseException(message=str(e), status_code=404)

    @classmethod
    async def get_by_fields(cls, filter: dict, model: ModelType, session: AsyncSession):
        """
            фильтр по нескольким полям
            filter = {<имя поля>: <искомое значение>, ...},
            AND
        """
        try:
            conditions = []
            for key, value in filter.items():
                column = getattr(model, key)
                if value is None:
                    conditions.append(column.is_(None))
                else:
                    conditions.append(column == value)
            stmt = select(model).where(and_(*conditions))
            result = await session.execute(stmt)
            # возвращает  instance
            return result.scalar_one_or_none()
        except Exception as e:
            raise AppBaseException(message=str(e), status_code=404)

    @classmethod
    async def get_all_count(cls, model: ModelType, session: AsyncSession) -> int:
        """ колитчество всех записей в таблице DELETE """
        # count_stmt = select(func.count()).select_from(model)
        count_stmt = cls.get_count(select(model), session)
        result = await session.execute(count_stmt).scalar()
        return result

    @classmethod
    async def search_by_enum(cls, enum: str,
                             model: Type[ModelType],
                             session: AsyncSession,
                             field_name: str = None) -> Optional[ModelType]:
        """
        поиск по ключевому полю. на входе enum. на выходе 1 запись
        """
        conditions = create_enum_conditions(model, enum, field_name)
        stmt = select(model).where(conditions).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    def apply_search_filter(cls, model: Union[Select[Tuple], ModelType], **kwargs):
        """
            переопределяемый метод.
            в kwargs - условия поиска
            применяет фильтры и возвращает
            1. если на входе model - выборку с selectinload
            2. на входе Select - просто select (count, ...)
        """
        if not isinstance(model, Select):   # подсчет количества
            query = cls.get_query(model)
        else:
            query = model
        search_str: str = kwargs.get('search_str')
        if search_str:
            search_cond = create_search_conditions2(cls.model, search_str)
            query = query.where(search_cond)
        return query

    @classmethod
    async def search(cls, search: str,
                     skip: int, limit: int,
                     model: ModelType, session: AsyncSession, ) -> tuple:
        """
            НЕ УДАЛЯТЬ !!! ИСПОЛЬЗУЕТСЯ В PREACT
            Поиск по всем заданным текстовым полям основной таблицы
            через raw sql и limit
        """
        try:
            # query = cls.get_query(model)
            query = cls.get_short_query(model)
            id_query, count_query = get_sql_search(query, search, limit=limit, offset=skip)
            # 1. Получаем список ID:
            compiled = id_query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            logger.warning(str(compiled))
            response = await session.execute(id_query)
            ids = response.scalars().all()
            # 2. Получаем общее кол-во:
            response = await session.execute(count_query)
            total = response.scalar()
            result = await cls.get_by_ids(ids, model, session)
            return result if result else [], total
        except Exception as e:
            raise AppBaseException(message=f'core.repository.error: {str(e)}', status_code=404)

    @classmethod
    async def search_all(
        cls, search: str, model: Type[ModelType], session: AsyncSession,
        limit: int = 20  # длина списка поисковой выдачи - что бы не уложить сервер
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        """
            НЕ УДАЛЯТЬ !!!
            ТОЖЕ ЧТО И search above but no pagination with limit
        """
        try:
            query = cls.get_query(model)
            id_query, count_query = get_sql_search(query, search, limit=limit)
            # 1. Получаем список ID:
            response = await session.execute(id_query)
            ids = response.scalars().all()
            result = await cls.get_by_ids(ids, model, session)
            return result if result else []
        except Exception as e:
            raise AppBaseException(message=str(e), status_code=404)

    @classmethod
    async def get_list_paging(cls, skip: int, limit: int,
                              model: ModelType, session: AsyncSession, ) -> Tuple[List[Dict], int]:
        """Запрос с загрузкой связей и пагинацией - ListView плиткой ? используется?"""
        stmt = cls.get_short_query(model).offset(skip).limit(limit)
        # fields = get_sqlalchemy_fields(stmt, exclude_list=['description*',])
        # stmt = select(*fields)

        # получение результата всех записей
        # total = cls.get_all_count(model, session)
        # result = await session.execute(stmt)
        # rows: List[Dict] = result.mappings().all()
        # return rows, total
        stmt = stmt.order_by(model.id.asc())
        # stmt = (cls.get_query(model).where(model.updated_at > after_date)
        #         .order_by(model.id.asc()))
        result = await cls.pagination(stmt, skip, limit, session)
        return result

    @classmethod
    async def get_list(cls, model: ModelType, session: AsyncSession, ) -> List[Dict]:
        """ Запрос с загрузкой связей без пагинации (для справочников)"""
        stmt = cls.get_short_query(model)
        # compiled_pg = stmt.compile(dialect=postgresql.dialect())
        result = await session.execute(stmt)
        res: List[ModelType] = result.scalars().all()
        return res

    @classmethod
    async def get_index(cls, model: ModelType, session: AsyncSession, **kwargs) -> int:
        """
        получение записей для
        заполнения поля search_content, по которому будет индексирование проводиться
        kwargs: {имя поля: значение, ...
        + search_content: True}
        если search_content: True - все записи
        если search_content: False - только пустые поля search_content (initial filing)
        """
        # 1. собираем фильтр из kwargs
        valid_fields = {key: value for key, value in kwargs.items() if hasattr(model, key)}
        stmt = cls.get_query(model).filter_by(**valid_fields)
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items

    @classmethod
    async def my_bulk_updates(cls, data: List[Dict[str, Any]], model: ModelType, session: AsyncSession):
        """
        массовове обновление данных. каждый словарь должен содержать 'id': int
        запускается через роутер
        """
        try:
            await session.execute(update(model), data)
        except Exception as e:
            raise AppBaseException(message=str(e), status_code=404)

    @classmethod
    async def get_image_id(cls, id: int, model: ModelType, session: AsyncSession) -> str:
        """
            получение image_id по id: для моделей основанных на
            app.core.models.image_mixin.ImageMixin
        """
        # проверка наличия поля image_id
        stmt = select(model.image_id).where(model.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_full_with_pagination(cls, skip: int, limit: int,
                                       model: ModelType, session: AsyncSession, ) -> tuple:
        """
            Запрос полного списка с загрузкой связей и пагинацией
            return Tuple[List[instances], int]
        """
        try:
            stmt = (cls.get_query(model).order_by(model.id.asc()))
            result = await cls.pagination(stmt, skip, limit, session)
            return result
        except Exception as e:
            raise AppBaseException(message=f'get_full_with_pagination.error; {str(e)}', status_code=404)

    @classmethod
    async def get_full(cls, model: ModelType, session: AsyncSession, limit: int = 20) -> list:
        """
            Запрос полного списка с загрузкой связей NO PAGINATION - ОСТОРОЖНО МОЖЕТ БЫТЬ ОЧЕНЬ БОЛЬШИМ
            return List[instance]
        """
        try:
            stmt = cls.get_query(model).order_by(model.id.asc())
            if limit:
                stmt = stmt.limit(limit)
            result = await cls.nonpagination(stmt, session)
            return result
        except Exception as e:
            raise AppBaseException(message=f'get_full.error; {str(e)}', status_code=404)

    @classmethod
    async def search_by_conditions(cls, filter: dict, model: ModelType, session: AsyncSession, **kwargs):
        """
            фильтр по нескольким полям, несколько значений для каждого поля
            filter = {<имя поля>: [<искомое значение>,...], ...},
        """
        try:
            stmt = select(model)
            for key, value in filter.items():
                column = getattr(model, key)
                if value is None:
                    stmt = stmt.where((column.is_(None)))
                elif isinstance(value, Union[List, Tuple]):
                    conditions = [column.icontains(val) for val in value]
                    stmt = stmt.where(or_(*conditions))
                else:
                    stmt = stmt.where(column == value)
            # from sqlalchemy.dialects import postgresql
            # compiled = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise AppBaseException(message=f'search_by_conditions.error; {str(e)}', status_code=404)

    @classmethod
    async def search_by_list_value_exact(cls, filter: List[Any], field: str, model: ModelType, session: AsyncSession,
                                         **kwargs):
        """
             фильтр по нескольким значениям поля (полное совпадение)
        """
        try:
            column = getattr(model, field)
            stmt = cls.get_query(model).where(column.in_(filter))
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise AppBaseException(message=f'search_by_list_value_exact.error; {str(e)}', status_code=404)

    @classmethod
    async def sync_items_by_path(cls,
                                 session: AsyncSession, current_model,  # Например, модель Category
                                 start_id: int, path_str: str, skip_keys: set
                                 ) -> int:
        """
            Синхронизирует search_content у всех Item, связанных с измененной записью.
            Решает проблему DuplicateAliasError через алиасы.
        """
        try:            # 1. Получаем классы моделей
            ItemModel = get_model_by_name('Item')
            DrinkModel = get_model_by_name('Drink')
            # Используем алиасы, чтобы SQLAlchemy не путалась при джоинах
            target_drink = aliased(DrinkModel)
            target_item = aliased(ItemModel)

            # 2. Строим запрос от текущей модели к целям (Item, Drink)
            stmt = select(target_item, target_drink).select_from(current_model)

            # 3. Динамическая цепочка JOIN по метаданным
            active_model_class = current_model
            path_parts = path_str.split('.')

            for part in path_parts:
                mapper = inspect(active_model_class)
                # Находим имя relationship
                rel_key = next(
                    (r.key for r in mapper.relationships if r.mapper.class_.__name__.lower() == part.lower()), None
                )

                if not rel_key:
                    raise AttributeError(f"Связь '{part}' не найдена в модели {active_model_class.__name__}")

                # Определяем, к какому классу прыгаем
                next_model_class = getattr(active_model_class, rel_key).property.mapper.class_

                # Подменяем на алиас, если дошли до Drink или Item
                if next_model_class == DrinkModel:
                    step_target = target_drink
                elif next_model_class == ItemModel:
                    step_target = target_item
                else:
                    step_target = next_model_class

                # Выполняем JOIN через атрибут отношения
                stmt = stmt.join(step_target, getattr(active_model_class, rel_key))
                active_model_class = next_model_class

            # 4. Фильтруем по ID и выполняем
            stmt = stmt.where(current_model.id == start_id)
            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                logger.info('sync_items_by_path. no records for update')
                return 0
            logger.info('sync_items_by_path 1')
            # 5. Обработка и обновление
            processed_drinks: list = []
            for item_obj, drink_obj in rows:
                if drink_obj.id not in processed_drinks:
                    drink_dict = drink_obj.to_dict_fast()
                    content = extract_text_ultra_fast(drink_dict, skip_keys).lower()
                    logger.info('sync_items_by_path 2')
                    processed_drinks.append(drink_obj.id)
                    logger.info('sync_items_by_path 3')
                    item_obj.search_content = content

            # 6. Принудительная синхронизация с БД
            await session.flush()
            logger.success(f'updated {len(rows)} records')
            return len(rows)
        except Exception as e:
            raise AppBaseException(message=f'sync_items_by_path.error; {str(e)}', status_code=404)

    @classmethod
    async def get_keyset(cls, model: ModelType, session: AsyncSession,
                         last_id: int = None,
                         limit: int = 15) -> dict:
        """
            постраничный вывод по keyset
            не знает сколько страниц всего, но быстрый доступ для страниц > 10
        """
        # Условие Keyset: (score < last_score) ИЛИ (score == last_score И id < last_id)
        stmt = cls.get_query(model)
        if last_id is not None:
            stmt = stmt.where(model.id < last_id)
        # Сортировка по score, затем по id для стабильности
        stmt = stmt.order_by(desc(model.id)).limit(limit)
        result = await session.execute(stmt)
        return result.all()
