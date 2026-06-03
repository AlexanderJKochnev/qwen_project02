# доработать если поналобится

from typing import List, Optional, Type, Generic
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.types import ModelType
# Абстрактный тип для моделей SQLAlchemy 2.0


class SearchRepositoryMixin(Generic[ModelType]):
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
