# доработать если поналобится

from typing import List, Optional
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession


class FoodRepository:
    @staticmethod
    def _normalize_expr(column_attr):
        """Вспомогательный метод для переиспользования нормализации поля"""
        return func.public.immutable_unaccent(func.lower(column_attr))
    
    @staticmethod
    def _normalize_value(value: str) -> str:
        """Вспомогательный метод для нормализации входящей строки поиска"""
        return value.strip()
    
    @classmethod
    async def find_by_exact_name(cls, session: AsyncSession, search_name: str) -> Optional[Food]:
        """
        1. Поиск по ТОЧНОМУ совпадению (Полностью задействует UNIQUE B-tree индекс).
        Ищет 'Café', 'cafe', 'CAFE' и т.д.
        """
        clean_name = cls._normalize_value(search_name)
        
        query = (select(Food).where(
                cls._normalize_expr(Food.name) == func.public.immutable_unaccent(func.lower(clean_name))
                ))
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def find_by_name_startswith(cls, session: AsyncSession, search_prefix: str) -> List[Food]:
        """
        2. Поиск по НАЧАЛУ СТРОКИ (Задействует B-tree индекс по принципу диапазона значений).
        Если передать 'Caf', найдет 'Café', 'Cafeteria', 'cafe' и т.д.
        """
        clean_prefix = cls._normalize_value(search_prefix)
        # Формируем паттерн для LIKE: 'искомая_строка%'
        like_pattern = f"{clean_prefix}%"
        
        query = (select(Food).where(
                # Благодаря знаку % строго в конце, B-tree индекс отработает моментально
                cls._normalize_expr(Food.name).like(
                        func.public.immutable_unaccent(func.lower(like_pattern))
                        )
                ))
        
        result = await session.execute(query)
        return list(result.scalars().all())
