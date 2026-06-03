# доработать если поналобится
from loguru import logger
from typing import Any, List, Optional, Tuple, Type, Generic
from sqlalchemy import select, func, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppBaseException
from app.core.types import ModelType
from app.core.utils.alchemy_utils import get_unaccent_search


# Абстрактный тип для моделей SQLAlchemy 2.0


class SearchRepositoryMixin:  # (Generic[ModelType]):
    """
    Универсальный CRUD-миксин для репозиториев.
    Предоставляет высокопроизводительный поиск по нормализованному полю 'name'
    для одиночных и составных функциональных индексов.
    """
    model: Type[ModelType]  # Здесь дочерний репозиторий укажет свою модель

    @classmethod
    def _normalize_expr(cls):
        """Возвращает скомпилированное SQL-выражение индекса для левой части WHERE"""
        return func.public.immutable_unaccent(func.lower(text(f"{cls.model.__tablename__}.name")))

    @classmethod
    def _normalize_value(cls, value: str) -> str:
        """Очищает входящую строку от пробелов по краям"""
        return value.strip()

    @classmethod
    async def find_by_exact_name(
            cls, session: AsyncSession, search_name: str, parent_id: Optional[int] = None
    ) -> Optional[ModelType]:
        """
        1. ПОЛНОЕ СОВПАДЕНИЕ (Index Scan).
        Универсален: если передан parent_id — использует весь составной индекс целиком.
        Если parent_id не передан — ищет только по имени во всей базе.
        """
        clean_name = cls._normalize_value(search_name)

        # Строим базовое условие по нашему функциональному индексу
        stmt = select(cls.model).where(
            cls._normalize_expr() == func.public.immutable_unaccent(func.lower(clean_name))
        )

        # Если это составной индекс и передан ID родителя, добавляем его в запрос
        if parent_id is not None:
            fk_field_name = getattr(cls.model, "__composite_fk_field__", None)
            if fk_field_name:
                stmt = stmt.where(text(f"{cls.model.__tablename__}.{fk_field_name} = :p_id")).params(p_id=parent_id)

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def find_by_name_startswith(
            cls, session: AsyncSession, search_prefix: str, parent_id: Optional[int] = None
    ) -> List[ModelType]:
        """
        2. ПОИСК ПО НАЧАЛУ СТРОКИ (B-tree префиксный диапазон).
        Благодаря знаку '%' строго в конце, PostgreSQL мгновенно находит данные.
        """
        clean_prefix = cls._normalize_value(search_prefix)
        like_pattern = f"{clean_prefix}%"

        stmt = select(cls.model).where(
            cls._normalize_expr().like(func.public.immutable_unaccent(func.lower(like_pattern)))
        )

        # Добавляем фильтрацию по родителю для составных индексов
        if parent_id is not None:
            fk_field_name = getattr(cls.model, "__composite_fk_field__", None)
            if fk_field_name:
                stmt = stmt.where(text(f"{cls.model.__tablename__}.{fk_field_name} = :p_id")).params(p_id=parent_id)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def get_sql_search(query, search_str: str, limit: int = 100, offset: int = 0,
                       mode: str = "startswith") -> Tuple:
        """
        оригинальный метод парсинга raw sql.
        ИЗМЕНЕНИЕ: Теперь генерирует условия, которые на 100% задействуют B-tree индекс unaccent.
        """
        raw_sql = str(
            query.compile(dialect=postgresql.dialect(), compile_kwargs={"render_postcompile_parameters": True})
        )

        select_part = raw_sql[len("SELECT "):raw_sql.find("FROM")].strip()
        from_part = raw_sql[raw_sql.find("FROM"):].strip()

        all_columns = [col.strip().split(" AS ")[0] for col in select_part.split(",")]
        name_cols = [col for col in all_columns if "name" in col.lower()]

        # --- ТУТ ЕДИНСТВЕННОЕ ИЗМЕНЕНИЕ ---
        # Очищаем входящую строку от пробелов
        clean_search = search_str.strip()

        if mode == "exact":
            # Полное совпадение: public.immutable_unaccent(lower(col)) = public.immutable_unaccent(lower('значение'))
            search_val = f"public.immutable_unaccent(lower('{clean_search}'))"
            where_clause = " OR ".join([f"public.immutable_unaccent(lower({col})) = {search_val}" for col in name_cols])
        else:
            # По префиксу (startswith): public.immutable_unaccent(lower(col)) LIKE public.immutable_unaccent(lower('значение%'))
            search_val = f"public.immutable_unaccent(lower('{clean_search}%'))"
            where_clause = " OR ".join(
                [f"public.immutable_unaccent(lower({col})) LIKE {search_val}" for col in name_cols]
            )
        # ----------------------------------

        main_table = from_part.split()[1]

        id_sql = f"SELECT DISTINCT {main_table}.id {from_part} WHERE {where_clause}"
        if limit:
            id_sql = f"{id_sql} LIMIT {limit}"
        if offset:
            id_sql = f"{id_sql} OFFSET {offset}"

        count_sql = f"SELECT COUNT(DISTINCT {main_table}.id) {from_part} WHERE {where_clause}"

        return text(id_sql), text(count_sql)

    @classmethod
    async def search(cls, search: str,
                     skip: int, limit: int,
                     model: ModelType, session: AsyncSession, ) -> tuple:
        """
            НЕ УДАЛЯТЬ !!! ИСПОЛЬЗУЕТСЯ В PREACT
            Поиск по всем заданным текстовым полям основной таблицы
            через raw sql и limit
        """
        logger.critical('this is SearchRepositoryMixin')
        try:
            # query = cls.get_query(model)
            query = cls.get_short_query(model)
            id_query, count_query = cls.get_sql_search(query, search, limit=limit, offset=skip)
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