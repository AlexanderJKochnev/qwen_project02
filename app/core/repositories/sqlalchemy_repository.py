# app/core/repositories/sqlalchemy_repository.py
"""
    переделать на ._mapping (.mappings().all()) (в результате словарь вместо объекта)
    get_all     result.mappings().all()
    get_by_id   result.scalar_one_or_none()
"""
from abc import ABCMeta
from datetime import datetime
from loguru import logger
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from sqlalchemy import and_, func, select, Select, update, desc, cast, Text, text, literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import Label
# from sqlalchemy.dialects import postgresql
# from sqlalchemy.sql.elements import ColumnElement
from app.core.utils.alchemy_utils import (create_enum_conditions,
                                          create_search_conditions2, ModelType)
from app.core.utils.alchemy_utils import get_sqlalchemy_fields
from app.service_registry import register_repo


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
    async def pagination(cls, stmt: Select, skip: int, limit: int, session: AsyncSession):
        """
            получает запрос, сдвиг и размер страницы, сессию
            возвращает список instances и кол-во записей
        """
        count_stmt = select(func.count()).select_from(stmt)
        total = await session.scalar(count_stmt) or 0
        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items, total

    @classmethod
    async def nonpagination(cls, stmt: Select, session: AsyncSession):
        """
            получает запрос, сдвиг и размер страницы, сессию
            возвращает список instances и кол-во записей
        """
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items

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
            stmt.offset(skip).limit(limit)
        response = await session.execute(stmt)
        matching_ids = [row[0] for row in response.fetchall()]
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
        items = [items_map[id_] for id_ in matching if id_ in items_map]
        return items

    @classmethod
    def item_exists(cls, id: int):
        # переопределеяемый метод, для получения списка ids of Item отфильтрованного по id в связанной таблице
        return None

    @classmethod
    async def invalidate_search_index(cls, id: int, item: ModelType, model: ModelType, session: AsyncSession):
        """ обнуление item.search_content в записях у которых child records updated"""
        try:
            stmp = update(item).where(cls.item_exists(id)).values({'search_content': None})
            # Компилируем специально для PostgreSQL
            # compiled = stmp.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            await session.execute(stmp)
        except Exception as e:
            raise Exception(f'fault of invalidate_search_index. {e}')

    @classmethod
    def get_short_query(cls, model: ModelType):
        """
            Переопределяемый метод.
            Возвращает select() только с нужными полями - использовать для list_view.
            По умолчанию — без связей.
        """
        """ пример
        stmt = (
        select(
            Drink.id,
            Drink.name,
            Subregion.name.label('subregion_name'),
            Region.name.label('region_name'),
            Country.name.label('country_name'),
            Subcategory.name.label('subcategory_name'),
            Category.name.label('category_name')
        )
        .select_from(Drink)
        .join(Drink.subregion)
        .join(Subregion.region)
        .join(Region.country)
        .join(Drink.subcategory)
        .join(Subcategory.category)
        .options(
            selectinload(Drink.foods).load_only(Food.id, Food.name),
            selectinload(Drink.varietals).load_only(Varietal.id, Varietal.name)
            )
        )
        """
        return select(model)

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
            error_str = str(e.orig).lower()
            original_error_str = str(e.orig)

            if 'unique constraint' in error_str or 'duplicate key' in error_str:
                # Extract field name and value from the error message
                field_info = cls._extract_field_info_from_error(original_error_str)
                return {
                    "success": False,
                    "error_type": "unique_constraint_violation",
                    "message": f"Нарушение уникальности: {original_error_str}",
                    "field_info": field_info
                }
            elif 'foreign key constraint' in error_str or 'fk_' in error_str:
                # Extract field name and value from the error message
                field_info = cls._extract_field_info_from_error(original_error_str)
                return {
                    "success": False,
                    "error_type": "foreign_key_violation",
                    "message": f"Нарушение внешнего ключа: {original_error_str}",
                    "field_info": field_info
                }
            return {
                "success": False,
                "error_type": "integrity_error",
                "message": f"Ошибка целостности данных: {original_error_str}"
            }
        except Exception as e:
            return {
                "success": False,
                "error_type": "database_error",
                "message": f"Ошибка базы данных при обновлении: {str(e)}"
            }

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
            import re
            table_match = re.search(r'"([^"]+)"', error_message)
            if table_match:
                field_info['table'] = table_match.group(1)

            # Extract the duplicate value
            value_match = re.search(r'\(([^)]+)\)=\(([^)]+)\)', error_message)
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
    async def get_all(cls, after_date: datetime, skip: int,
                      limit: int, model: ModelType, session: AsyncSession, ) -> tuple:
        """
            Запрос с загрузкой связей и пагинацией
            return Tuple[List[instances], int]
        """
        stmt = (cls.get_query(model).where(model.updated_at > after_date)
                .order_by(model.id.asc()))
        result = await cls.pagination(stmt, skip, limit, session)
        return result
        """
        count_stmt = select(func.count()).select_from(stmt)
        total = await session.scalar(count_stmt) or 0
        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        items = result.scalars().all()
        return items, total
        """

    @classmethod
    async def get(cls, after_date: datetime, model: ModelType, session: AsyncSession, ) -> list:
        """
            Запрос с загрузкой связей NO PAGINATION
            return List[instance]
        """
        stmt = cls.get_query(model).where(model.updated_at > after_date).order_by(model.id.asc())
        result = await cls.nonpagination(stmt, session)
        return result

    @classmethod
    async def get_by_field(cls, field_name: str, field_value: Any, model: ModelType, session: AsyncSession):
        """
            не гибкий поиск по одному полю. оставлен для совместимости. лучше использовать
            get_by_fields
        """
        try:
            stmt = select(model).where(getattr(model, field_name) == field_value)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise Exception(f'repo.get_by_field: {field_name=} {field_value=}, {model.__name__=}, {e}')

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
            stmt = select(model).where(and_(*conditions)).limit(1)
            # print(f"DEBUG: session object: {session}")
            # print(f"DEBUG: session type: {type(session)}")
            # print(f"DEBUG: hasattr execute: {hasattr(session, 'execute')}")
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise Exception(f'repo.get_by_fields: {filter=}, {model.__name__=}, {e}')

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
            logger.error(f'ошибка search: {e}')

    @classmethod
    async def search_all(
            cls, search: str, model: Type[ModelType], session: AsyncSession) -> Optional[List[ModelType]]:
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
            result = await session.execute(query)
            records = result.scalars().all()
            return records
        except Exception as e:
            print(f'{e}')

    @classmethod
    async def get_list_paging(cls, skip: int, limit: int,
                              model: ModelType, session: AsyncSession, ) -> Tuple[List[Dict], int]:
        """Запрос с загрузкой связей и пагинацией - ListView плиткой"""
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
            logger.error(f'bulf_update.error: {model.__name__}. {e}')

    @classmethod
    async def search_geans(cls, search: str, relevance: Label,
                           skip: int, limit: int,
                           model: ModelType, session: AsyncSession, ) -> tuple:
        """
            Поисковый запрос
        """
        try:
            total_count = 0
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
            items = await cls.get_greenlet(model, matching, session)
            return items, total_count
        except Exception as e:
            logger.error(f'search_geans.error: {e}')
            raise Exception(f'search_geans.error: {e}')

    @classmethod
    async def search_geans_all(
            cls, search: str, relevance: Label, model: ModelType,
            session: AsyncSession, ) -> tuple:
        """
            Поисковый запрос
        """
        matchnig = await cls.get_match(model, relevance, search, session)
        items = await cls.get_greenlet(model, matchnig, session)
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
