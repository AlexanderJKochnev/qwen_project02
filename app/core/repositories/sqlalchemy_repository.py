# app/core/repositories/sqlalchemy_repository.py
"""
    переделать на ._mapping (.mappings().all()) (в результате словарь вместо объекта)
    get_all     result.mappings().all()
    get_by_id   result.scalar_one_or_none()
"""
from functools import lru_cache
from abc import ABCMeta
from re import search as research
from datetime import datetime
from loguru import logger
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union
from sqlalchemy import and_, func, Row, RowMapping, select, Select, update, desc, cast, Text, text, literal, \
    literal_column, or_
from sqlalchemy import inspect
from sqlalchemy.orm import load_only, aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import Label

from app.core.hash_norm import get_hashes_for_item
from app.core.models.base_model import get_model_by_name
from app.core.exceptions import AppBaseException
# from sqlalchemy.dialects import postgresql
# from sqlalchemy.sql.elements import ColumnElement
from app.core.utils.alchemy_utils import (create_enum_conditions, get_sqlalchemy_fields,
                                          create_search_conditions2, get_field_list)
from app.core.utils.reindexation import extract_text_ultra_fast
from app.service_registry import register_repo
from app.core.types import ModelType
from app.core.config.project_config import settings

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


class Repository(metaclass=RepositoryMeta):
    __abstract__ = True
    model: ModelType

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
        # from sqlalchemy.dialects import postgresql
        count_stmt = select(func.count()).select_from(stmt)
        # compiled_pg = count_stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        total = await session.scalar(count_stmt) or 0
        if total == 0:
            return None, total
        stmt = stmt.offset(skip).limit(limit)
        # compiled_pg = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items, total

    @classmethod
    async def nonpagination(cls, stmt: Select, session: AsyncSession):
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
    def item_exists(cls, id: int):
        # переопределеяемый метод, для получения списка ids of Item отфильтрованного по id в связанной таблице
        return None

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
    async def get_count(cls, after_date: datetime, model: ModelType, session: AsyncSession) -> int:
        """ подсчет количества записей после указанной даты"""
        count_stmt = select(func.count()).select_from(model).where(model.updated_at > after_date)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar()   # ok
        return total

    @classmethod
    async def get_all_count(cls, model: ModelType, session: AsyncSession) -> int:
        """ колитчество всех записей в таблице DELETE """
        count_stmt = select(func.count()).select_from(model)
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
        Поиск по всем заданным текстовым полям основной таблицы
        если указана pagination - возвращвет pagination
        :param search_str:  текстовое условие поиска
        :type search_str:   str
        :param model:       модель
        :type model:        sqlalchemy model
        :param session:     async session
        :type session:      async session
        :param skip:        сдвиг на кол-во записей (для пагинации)
        :type skip:         int
        :param limit:       кол-во записей
        :type limit:        int
        :param and_condition:   дополнительные условия _AND
        :type and_condition:    dict
        :return:                Optional[List[ModelType]]
        :rtype:                 Optional[List[ModelType]]
        """
        try:
            kwargs: dict = {}
            kwargs['search_str'] = search
            query = cls.apply_search_filter(cls.get_query(model), **kwargs)
            total = 0
            # общее кол-во записей удовлетворяющих условию
            count_stmt = cls.apply_search_filter(select(func.count()).select_from(cls.get_query(model)),
                                                 **kwargs)
            result = await session.execute(count_stmt)
            total = result.scalar()     # ok
            query = query.limit(limit).offset(skip)
            result = await session.execute(query)
            records = result.scalars().all()
            return (records if records else [], total)
        except Exception as e:
            raise AppBaseException(message=str(e), status_code=404)

    @classmethod
    async def search_all(
        cls, search: str, model: Type[ModelType], session: AsyncSession,
        limit: int = 20  # длина списка поисковой выдачи - что бы не уложить сервер
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        """
        Поиск по всем заданным текстовым полям основной таблицы
        если указана pagination - возвращвет pagination
        :param search_str:  текстовое условие поиска
        :type search_str:   str
        :param model:       модель
        :type model:        sqlalchemy model
        :param session:     async session
        :type session:      async session
        :param skip:        сдвиг на кол-во записей (для пагинации)
        :type skip:         int
        :param limit:       кол-во записей
        :type limit:        int
        :param and_condition:   дополнительные условия _AND
        :type and_condition:    dict
        :return:                Optional[List[ModelType]]
        :rtype:                 Optional[List[ModelType]]
        """
        try:
            kwargs: dict = {}
            kwargs['search_str'] = search
            query = cls.apply_search_filter(cls.get_query(model), **kwargs)
            if limit:
                query = query.limit(limit)
            result = await session.execute(query)
            records = result.scalars().all()
            return records
        except Exception as e:
            raise AppBaseException(message=str(e), status_code=404)

    @classmethod
    async def get_list_paging(cls, skip: int, limit: int,
                              model: ModelType, session: AsyncSession, ) -> Tuple[List[Dict], int]:
        """Запрос с загрузкой связей и пагинацией - ListView плиткой ? не используется?"""
        stmt = cls.get_short_query(model).offset(skip).limit(limit)
        fields = get_sqlalchemy_fields(stmt, exclude_list=['description*',])
        stmt = select(*fields)

        # получение результата всех записей
        total = cls.get_all_count(model, session)
        result = await session.execute(stmt)
        rows: List[Dict] = result.mappings().all()
        return rows, total

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
    async def search_geans(cls, search: str, relevance: Label,
                           skip: int, limit: int,
                           model: ModelType, session: AsyncSession, ) -> tuple:
        """
            Поисковый запрос
        """
        try:
            total_count = 0
            if search:
                # получение ранжированного списка id
                matching = await cls.get_match(model, relevance, search, session, skip, limit)
                if not matching:
                    return [], 0
                if len(matching) <= limit:
                    total_count = len(matching)
                else:
                    # 2. Считаем общее количество подходящих записей
                    count_stmt = (select(func.count())
                                  .select_from(model)
                                  .where(cast(literal(search), Text).op("<%")(model.search_content)))
                    total_count = await session.scalar(count_stmt) or 0
                # 3. load all greenlets
                # items = await cls.get_greenlet(model, matching, session, skip, limit)
            else:   # пустой поисковый запрос
                count_stmt = select(func.count()).select_from(model)
                total_count = await session.scalar(count_stmt) or 0
                matching = []
            items = await cls.get_greenlet(model, matching, session)
            return items, total_count
        except Exception as e:
            raise AppBaseException(message=f'search_geans.error; {str(e)}', status_code=404)

    @classmethod
    async def search_geans_all(
        cls, search: str, relevance: Label, model: ModelType,
        session: AsyncSession,
        limit: int = 20  # длина списка поисковой выдачи - что бы не уложить сервер
    ) -> tuple:
        """
            Поисковый запрос
        """
        matching: list = []
        matching: list = await cls.get_match(model, relevance, search, session, limit)
        items = await cls.get_greenlet(model, matching, session)
        return items

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
    async def search_fts(cls, search: str, skip: int, limit: int,
                         model: ModelType, session: AsyncSession) -> Tuple[Any, int]:
        """ полнотекстовый поиск """
        try:
            condition = model.search_vector.bool_op("@@")(func.to_tsquery(literal_column("'simple'"),
                                                                          search))
            # ниже - ищет только целые слова
            # condition = model.search_vector.bool_op("@@")(func.websearch_to_tsquery(
            #     literal_column("'simple'"), formatted_query)
            # )
            count_stmt = select(func.count()).select_from(model).where(condition)
            total = await session.execute(count_stmt)
            total_count = total.scalar() or 0
            stmp = cls.get_query(model).where(condition).offset(skip).limit(limit)
            # compiled = stmp.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            # logger.error(f'{compiled.string=}')
            result = await session.execute(stmp)
            items = result.scalars().all()
            return items, total_count
        except Exception as e:
            raise AppBaseException(message=f'search_fts.error; {str(e)}', status_code=404)

    @classmethod
    async def search_fts_all(cls, search: str, model: ModelType,
                             session: AsyncSession,
                             limit: int = 20  # длина списка поисковой выдачи - что бы не уложить сервер
                             ) -> Tuple[Any, int]:
        """ полнотекстовый поиск without pagination"""
        try:
            # formatted_query = " & ".join(search.split())
            # formatted_query = " & ".join([f"{word}:*" for word in search.split()])
            condition = model.search_vector.bool_op("@@")(func.to_tsquery(literal_column("'simple'"),
                                                                          search))
            stmp = cls.get_query(model).where(condition).limit(limit)
            # compiled = stmp.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            # logger.error(f'{compiled=}')
            result = await session.execute(stmp)
            items = result.scalars().all()
            return items
        except Exception as e:
            raise AppBaseException(message=f'search_fts_all.error; {str(e)}', status_code=404)

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
        try:
            # 1. Получаем классы моделей
            ItemModel = get_model_by_name('Item')
            DrinkModel = get_model_by_name('Drink')

            # Используем алиасы, чтобы SQLAlchemy не путалась при джоинах
            target_drink = aliased(DrinkModel)
            target_item = aliased(ItemModel)

            # 2. Строим запрос от текущей модели (Category) к целям (Item, Drink)
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
                return 0

            # 5. Обработка и обновление
            processed_drinks: list = []
            for item_obj, drink_obj in rows:
                if drink_obj.id not in processed_drinks:
                    # Логика как в reindex_items
                    drink_dict = drink_obj.to_dict()
                    content = extract_text_ultra_fast(drink_dict, skip_keys).lower()
                    processed_drinks.append(drink_obj.id)
                    item_obj.word_hashes = get_hashes_for_item(content)
                    # строку ниже удалить после тестирования хэш индекса
                    item_obj.search_content = content

            # 6. Принудительная синхронизация с БД
            await session.flush()

            return len(rows)
        except Exception as e:
            raise AppBaseException(message=f'sync_items_by_path.error; {str(e)}', status_code=404)

    @classmethod
    async def run_sync_background(
            cls, start_model: ModelType, start_id: int, path_str: str, session_factory, skip_keys: set
    ):
        """
        Фоновая обертка: создает новую сессию и запускает синхронизацию.
        """
        logger.warning(f'run_sync_background {start_id=}, {path_str=}')
        async with session_factory() as session:
            try:
                # Получаем саму модель по имени
                current_model = start_model  # get_model_by_name(start_model_name)
                logger.warning('run_sync_backgrounng 1')
                # Запускаем наш отлаженный метод
                updated_count = await cls.sync_items_by_path(
                    session=session, current_model=current_model, start_id=start_id, path_str=path_str,
                    skip_keys=skip_keys
                )
                logger.warning('run_sync_background 2')
                # Фиксируем изменения
                await session.commit()
                logger.info(
                    f"Background Sync: Обновлено {updated_count} записей Item для {start_model.__name__}:{start_id}"
                )

            except Exception as e:
                await session.rollback()
                error_msg = f"Background Sync Error for {start_model.__name__}:{start_id}: {e}"
                logger.error(error_msg)
                # просто информируем - не прерываем работу?

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

    @classmethod
    @lru_cache(maxsize=2000)
    async def get_cached_total_count(cls, model: ModelType, session: AsyncSession, hashes_tuple: tuple) -> int:
        """
        Кэширует общее количество найденных записей.
        ВАЖНО: lru_cache не поддерживает списки, поэтому передаем tuple.
        для моделей с хэщ индексом
        """
        if not hashes_tuple:
            return 0

        hashes = list(hashes_tuple)
        stmt = (select(func.count()).select_from(model).where(model.word_hashes.bool_op("&&")(hashes)))
        result = await session.execute(stmt)
        return result.scalar() or 0

    # В Service Layer вызываем так:
    # Превращаем список хешей в кортеж для кэша
    # hashes_tuple = tuple(sorted(all_hashes))
    # total_count = await get_cached_total_count(session, hashes_tuple)

    @classmethod
    async def get_search_metadata(cls, model: ModelType, session: AsyncSession, hashes: List[int]):
        """
        Получает частоты слов для расчета весов и общее кол-во записей.
        """
        # 1. Получаем частоты из WordHash
        from app.support.hashing.model import WordHash
        stats_stmt = select(WordHash.hash, WordHash.freq).where(WordHash.hash.in_(hashes))
        stats_res = await session.execute(stats_stmt)
        word_stats: dict = {r.hash: r.freq for r in stats_res.all()}
        hashes_tuple = tuple(sorted(hashes))
        # 2. Получаем Total Count (первый раз по настоящему затем из кэша)
        total_count = await cls.get_cached_total_count(model, session, hashes_tuple)
        return word_stats, total_count

    @classmethod
    async def find_items_hybrid(
            cls, model: ModelType,
            session: AsyncSession, word_weights: dict[int, float],  # hash -> weight
            last_score: Optional[float] = None, last_id: Optional[int] = None, limit: int = 15
    ) -> List[dict]:
        """
        Keyset пагинация с динамическим расчетом SCORE в БД.
        """
        hashes = list(word_weights.keys())
        # Строим CASE для скоринга
        case_parts = [f"CASE WHEN word_hashes @> ARRAY[{h}::bigint] THEN {w:.8f} ELSE 0 END" for h, w in
                      word_weights.items()]
        # score_sql = f"({' + '.join(case_parts)})"
        score_sql = f"ROUND(CAST(({' + '.join(case_parts)}) AS numeric), 4)"
        # Базовый запрос
        query = cls.get_query(model)
        stmt = query.add_columns(text(f"{score_sql} AS score"))  # добавляем колонку
        stmt = stmt.where(model.word_hashes.bool_op("&&")(hashes))
        # Keyset фильтрация (якорь)
        if last_score is not None and last_id is not None:
            # Используем строгое кортежное сравнение
            stmt = stmt.where(text(f"({score_sql}, id) < (:ls, :li)"))
            params = {"ls": last_score, "li": last_id}
        else:
            params = {}
        # Сортировка: Сначала вес, потом ID (для детерминированности)
        stmt = stmt.order_by(text(f"{score_sql} DESC"), model.id.desc()).limit(limit + 1)
        result = await session.execute(stmt, params)
        return [{'score': score, **item.to_dict_fast()} for item, score in result]

    @classmethod
    async def get_hashes_by_prefix(cls, session: AsyncSession, prefix: str, limit: int = 50) -> List[ModelType]:
        """
        Поиск хешей в словаре по префиксу последнего слова.
        """
        from app.support.hashing.model import WordHash
        stmt = (select(WordHash.hash).where(WordHash.word.like(f"{prefix.lower()}%")).order_by(
                WordHash.freq.desc()
                ).limit(limit))
        res = await session.execute(stmt)
        return res.scalars().all()
