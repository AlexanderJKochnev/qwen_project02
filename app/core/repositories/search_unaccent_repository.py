# доработать если поналобится
from loguru import logger
from typing import Any, List, Optional, Type, Generic
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

    @classmethod
    async def search(
            cls, search: str, skip: int, limit: int, model: Any, session: AsyncSession, mode: str = "startswith"
            # Можно передать "exact" для точного поиска
    ) -> tuple:
        """
        Высокопроизводительный поиск по всем связанным текстовым полям 'Name'
        с использованием B-tree функционального индекса unaccent.
        """
        try:
            logger.critical('this is SearchRepositoryMixin')
            # Получаем базовый запрос (JOIN'ы и связи выгружаются из вашего get_short_query)
            query = cls.get_short_query(model)

            # Строим запросы на ID и COUNT через AST-инспекцию SQLAlchemy
            id_query, count_query = get_unaccent_search(
                query=query, search_str=search, mode=mode, limit=limit, offset=skip
            )

            # Логируем скомпилированный SQL для отладки индексов
            compiled = id_query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
            logger.warning(f"🎰 INDEX SEARCH SQL: {str(compiled)}")

            # 1. Получаем список ID по индексу
            response = await session.execute(id_query)
            ids = response.scalars().all()

            # 2. Получаем общее количество
            response = await session.execute(count_query)
            total = response.scalar() or 0

            # 3. Выгружаем полные объекты по списку ID
            result = await cls.get_by_ids(ids, model, session)

            return result if result else [], total

        except Exception as e:
            raise AppBaseException(
                message=f'core.repository.unaccent_search.error: {str(e)}', status_code=404
            )
