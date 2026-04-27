# app/support/drink/repository.py
from typing import List, Optional, Type
from loguru import logger
from sqlalchemy import func, select, exists, or_
from sqlalchemy.dialects import postgresql  # NOQA: F401
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, load_only
from app.core.exceptions import AppBaseException
from app.core.utils.alchemy_utils import get_field_list
from app.support.producer.model import Producer
from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support import Drink, Region, Subregion, Subcategory, Site
from app.support.food.model import Food
from app.support.drink.model import DrinkFood, DrinkVarietal


class DrinkRepository(Repository):
    model = Drink

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == id
        )

    @classmethod
    def get_selectin(cls):
        return (selectinload(Drink.site).selectinload(Site.subregion).selectinload(Subregion.region).selectinload(
                Region.country),
                selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness),
                selectinload(Drink.food_associations).selectinload(DrinkFood.food).selectinload(Food.superfood),
                selectinload(Drink.varietal_associations).selectinload(DrinkVarietal.varietal),
                selectinload(Drink.source),
                selectinload(Drink.producer).selectinload(Producer.producertitle),
                selectinload(Drink.parcel),
                selectinload(Drink.designation),
                selectinload(Drink.classification),
                selectinload(Drink.vintageconfig))

    @classmethod
    def get_query(cls, model: ModelType):
        """ Добавляем загрузку связи с relationships
            Обратить внимание! для последовательной загрузки использовать точку.
            параллельно запятая
        """
        return select(Drink).options(*cls.get_selectin())

    @classmethod
    def get_short_query(cls, model: Drink, field1: tuple = ('id', 'title', 'subtitle')):
        """
            Возвращает список модели только с нужными полями остальные None
            - использовать для list_view и вообще где только можно.
            для моделей с зависимостями - переопределить
        """
        fields = get_field_list(model, starts=field1)
        return select(model).options(load_only(*fields))

    @classmethod
    def get_joined(cls, drink_ids):
        return select(Drink).where(Drink.id.in_(drink_ids)).options(
            joinedload(Drink.site).joinedload(Site.subregion).joinedload(Subregion.region),
            joinedload(Drink.subcategory).joinedload(Subcategory.category),
            joinedload(Drink.sweetness),
            joinedload(Drink.food_associations).joinedload(DrinkFood.food).joinedload(Food.superfood),
            joinedload(Drink.varietal_associations).joinedload(DrinkVarietal.varietal),
            joinedload(Drink.source),
            joinedload(Drink.producer).joinedload(Producer.producertitle),
            joinedload(Drink.parcel),
            joinedload(Drink.designation),
            joinedload(Drink.classification),
            joinedload(Drink.vintageconfig)
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
            raise AppBaseException(message=f'search_in_main_table.error; {str(e)}', status_code=404)

    @classmethod
    async def search_by_trigram_index(cls, search_str: str, model: ModelType, session: AsyncSession,
                                      skip: int = None, limit: int = None,
                                      category_enum: str = None,
                                      country_enum: str = None):
        """
            DEPRECATED
            Поиск элементов с использованием триграммного индекса УДАЛИТЬ НЕ РАБОТАЕТ
        """
        try:
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
        except Exception as e:
            raise AppBaseException(message=f'search_by_trigramm_index.error; {str(e)}', status_code=404)

    @classmethod
    async def search(
            cls, search: str, skip: int, limit: int, model: ModelType, session: AsyncSession, ) -> tuple:
        """
            Поиск по всем заданным текстовым полям основной таблицы
        """
        try:
            from app.core.config.project_config import settings
            langs = settings.lang_suffixes
            logger.warning(langs)
            # query = cls.get_query(model)
            query = cls.get_short_query(model)
            fields = ['title', 'subtitle', 'title_ru', 'subtitle']
            conditions = [getattr(model, f'{key}{lang}').icontains(search) for key in fields for lang in langs]
            query = query.where(or_(*conditions))
            total = cls.get_count(query, session)
            query = query.order_by('title').offset(skip).limit(limit)
            compiled = query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            logger.warning(str(compiled))
            response = await session.execute(query)
            ids = response.scalars().all()
            result = await cls.get_by_ids(ids, model, session)
            return result if result else [], total
        except Exception as e:
            raise AppBaseException(message=f'core.repository.error: {str(e)}', status_code=404)


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
