# app/support/drink/repository.py
from typing import List, Optional, Type

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy import select

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.support.region.model import Region
from app.support.subcategory.model import Subcategory
from app.support.subregion.model import Subregion


class DrinkRepository(Repository):
    model = Drink

    @classmethod
    def get_query_back(cls):
        """Returns a query to select Item IDs related to this model"""
        return select(Item.id).join(Drink, Item.drink_id == Drink.id)

    @classmethod
    def get_query(csl, model: ModelType):
        """ Добавляем загрузку связи с relationships
            Обратить внимание! для последовательной загрузки использовать точку.
            параллельно запятая
        """
        return select(Drink).options(selectinload(Drink.subregion).
                                     selectinload(Subregion.region).
                                     selectinload(Region.country),
                                     selectinload(Drink.subcategory).
                                     selectinload(Subcategory.category),
                                     selectinload(Drink.sweetness),
                                     # selectinload(Drink.foods),
                                     selectinload(Drink.food_associations),  # .joinedload(DrinkFood.food),
                                     # selectinload(Drink.varietals),
                                     selectinload(Drink.varietal_associations),
                                     )

    @classmethod
    async def search_in_main_table(cls,
                                   search_str: str,
                                   model: Type[Drink],
                                   session: AsyncSession,
                                   skip: int = None,
                                   limit: int = None,
                                   category_enum: str = None,
                                   country_enum: str = None) -> Optional[List[ModelType]]:
        """ Поиск по всем заданным текстовым полям основной таблицы
            Gроверить и удалить НЕ ИСПОЛЬЗХУЕТСЯ
        """
        try:
            query = cls.get_query(model)

            # Apply category filter if provided
            if category_enum:
                from app.support.subcategory.model import Subcategory
                from app.support.category.model import Category
                from app.core.utils.alchemy_utils import create_enum_conditions
                category_cond = create_enum_conditions(Category, category_enum)
                query = (query
                         .join(Drink.subcategory)
                         .join(Subcategory.category).where(category_cond))

            # Apply country filter if provided
            if country_enum:
                from app.support.country.model import Country
                from app.support.region.model import Region
                from app.support.subregion.model import Subregion
                from app.core.utils.alchemy_utils import create_enum_conditions
                country_cond = create_enum_conditions(Country, country_enum)
                query = (query.join(Drink.subregion)
                         .join(Subregion.region)
                         .join(Region.country).where(country_cond))

            # Apply search filter if provided
            if search_str:
                from app.core.utils.alchemy_utils import create_search_conditions2
                search_cond = create_search_conditions2(Drink, search_str)
                query = query.where(search_cond)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await session.execute(count_query)
            total = count_result.scalar()

            if total == 0:
                return [], 0

            # Apply pagination
            if skip is not None:
                query = query.offset(skip)
            if limit is not None:
                query = query.limit(limit)

            result = await session.execute(query)
            records = result.scalars().all()

            return records, total
        except Exception as e:
            print(f'search_in_main_table.error: {e}')

    @classmethod
    async def search_by_trigram_index(cls, search_str: str, model: ModelType, session: AsyncSession,
                                      skip: int = None, limit: int = None,
                                      category_enum: str = None,
                                      country_enum: str = None):
        """Поиск элементов с использованием триграммного индекса"""
        from sqlalchemy.types import String

        if search_str is None or search_str.strip() == '':
            # Если search_str пустой, возвращаем все записи с пагинацией
            query = cls.get_query(model)

            # Apply category filter if provided
            if category_enum:
                from app.support.subcategory.model import Subcategory
                from app.support.category.model import Category
                from app.core.utils.alchemy_utils import create_enum_conditions
                category_cond = create_enum_conditions(Category, category_enum)
                query = (query
                         .join(Drink.subcategory)
                         .join(Subcategory.category).where(category_cond))

            # Apply country filter if provided
            if country_enum:
                from app.support.country.model import Country
                from app.support.region.model import Region
                from app.support.subregion.model import Subregion
                from app.core.utils.alchemy_utils import create_enum_conditions
                country_cond = create_enum_conditions(Country, country_enum)
                query = (query.join(Drink.subregion)
                         .join(Subregion.region)
                         .join(Region.country).where(country_cond))

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await session.execute(count_query)
            total = count_result.scalar()

            # Apply pagination
            if skip is not None:
                query = query.offset(skip)
            if limit is not None:
                query = query.limit(limit)

            result = await session.execute(query)
            records = result.scalars().all()

            return records, total

        # Создаем строку для поиска с использованием триграммного индекса
        # Используем ту же логику, что и в индексе drink_trigram_idx_combined
        search_expr = get_drink_search_expression(Drink)

        query = cls.get_query(model).where(
            search_expr.cast(String).ilike(f'%{search_str}%')
        )

        # Apply category filter if provided
        if category_enum:
            from app.support.subcategory.model import Subcategory
            from app.support.category.model import Category
            from app.core.utils.alchemy_utils import create_enum_conditions
            category_cond = create_enum_conditions(Category, category_enum)
            query = (query
                     .join(Drink.subcategory)
                     .join(Subcategory.category).where(category_cond))

        # Apply country filter if provided
        if country_enum:
            from app.support.country.model import Country
            from app.support.region.model import Region
            from app.support.subregion.model import Subregion
            from app.core.utils.alchemy_utils import create_enum_conditions
            country_cond = create_enum_conditions(Country, country_enum)
            query = (query.join(Drink.subregion)
                     .join(Subregion.region)
                     .join(Region.country).where(country_cond))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar()

        # Apply pagination
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        result = await session.execute(query)
        records = result.scalars().all()

        return records, total


def get_drink_search_expression(cls):
    """
        для поиска по триграммному индексу

    """
    return (func.coalesce(cls.title, '') + ' ' + func.coalesce(cls.title_ru, '') + ' ' + func.coalesce(
            cls.title_fr, ''
            ) + ' ' + func.coalesce(cls.subtitle, '') + ' ' + func.coalesce(cls.subtitle_ru, '') + ' ' + func.coalesce(
            cls.subtitle_fr, ''
            ) + ' ' + func.coalesce(cls.description, '') + ' ' + func.coalesce(
            cls.description_ru, ''
            ) + ' ' + func.coalesce(
            cls.description_fr, ''
            ) + ' ' + func.coalesce(cls.recommendation, '') + ' ' + func.coalesce(
            cls.recommendation_ru, ''
            ) + ' ' + func.coalesce(
            cls.recommendation_fr, ''
            ) + ' ' + func.coalesce(cls.madeof, '') + ' ' + func.coalesce(cls.madeof_ru, '') + ' ' + func.coalesce(
            cls.madeof_fr, ''
            ))
