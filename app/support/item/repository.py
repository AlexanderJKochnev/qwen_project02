# app/support/Item/repository.py

from sqlalchemy.orm import selectinload
from typing import Optional, List, Type, Tuple, Union, Dict, Any
from sqlalchemy import func, select, Select, or_, Row, literal_column, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import String
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.drink.model import Drink, DrinkFood, DrinkVarietal
from app.support.drink.repository import DrinkRepository  # , get_drink_search_expression
from app.support.item.model import Item
from app.support.country.model import Country
from app.support.region.model import Region
from app.support.subregion.model import Subregion
from app.support.subcategory.model import Subcategory
from app.support.category.model import Category
from app.core.utils.alchemy_utils import ModelType, create_enum_conditions, create_search_conditions2
from app.core.services.logger import logger


# from app.core.config.database.db_noclass import get_db


# ItemRepository = RepositoryFactory.get_repository(Item)
class ItemRepository(Repository):
    model = Item

    @classmethod
    def get_query2(csl, model: ModelType):
        """ Добавляем загрузку связи с relationships
            Обратить внимание! для последовательной загрузки использовать точку.
            параллельно запятая
        """
        return select(Item).options(selectinload(Item.drink).
                                    selectinload(Drink.subregion).
                                    selectinload(Subregion.region).
                                    selectinload(Region.country),
                                    selectinload(Item.drink).
                                    selectinload(Drink.subcategory).
                                    selectinload(Subcategory.category),
                                    selectinload(Drink.sweetness),
                                    selectinload(Item.drink).
                                    selectinload(Drink.foods),
                                    selectinload(Drink.food_associations).joinedload(DrinkFood.food),
                                    selectinload(Drink.varietals),
                                    selectinload(Drink.varietal_associations).joinedload(DrinkVarietal.varietal))

    @classmethod
    def get_query(cls, model: ModelType):
        return select(model).options(
            selectinload(Item.drink).options(
                selectinload(Drink.subregion).options(
                    selectinload(Subregion.region).options(
                        selectinload(Region.country)
                    )
                ),
                selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness), selectinload(Drink.foods),
                selectinload(Drink.food_associations).joinedload(DrinkFood.food), selectinload(Drink.varietals),
                selectinload(Drink.varietal_associations).joinedload(DrinkVarietal.varietal)
            ),
        )

    @classmethod
    def get_query_for_list_view(cls):
        """ get_query для запроса lit_view """
        return selectinload(Item.drink).options(
            selectinload(Drink.subregion).options(
                selectinload(Subregion.region).options(
                    selectinload(Region.country)
                )
            ),
            selectinload(Drink.subcategory).selectinload(Subcategory.category),
            selectinload(Drink.sweetness)
        )

    @classmethod
    async def search_in_main_table(cls,
                                   search_str: str,
                                   model: Type[Item],
                                   session: AsyncSession,
                                   skip: int = None,
                                   limit: int = None,
                                   category_enum: str = None,
                                   country_enum: str = None) -> Optional[List[ModelType]]:
        """Поиск по всем заданным текстовым полям основной таблицы
            НЕ ИСПОЛЬЗУЕТСЯ УДАЛИТЬ
        """
        try:
            # ищем в Drink (диапазон расширяем в два раза что бы охватить все Items
            # ищем category_id:
            dlimit = limit * 2 if limit else limit
            if skip and limit:
                dskip = skip if skip == 0 else skip - limit
            else:
                dskip = None
            drinks, count = await DrinkRepository.search_in_main_table(search_str, Drink, session,
                                                                       skip=dskip, limit=dlimit,
                                                                       category_enum=category_enum,
                                                                       country_enum=country_enum)
            if count == 0:
                records = []
                total = 0
            else:
                conditions = [a.id for a in drinks]
                query = cls.get_query(model).where(model.drink_id.in_(conditions))
                # получаем общее количество записей удовлетворяющих условию
                count = select(func.count()).select_from(model).where(model.drink_id.in_(conditions))
                result = await session.execute(count)
                total = result.scalar()
                # Добавляем пагинацию если указано
                if limit is not None:
                    query = query.limit(limit)
                if skip is not None:
                    query = query.offset(skip)
                result = await session.execute(query)
                records = result.scalars().all()
            return (records if records else [], total)
        except Exception as e:
            logger.error(f'ошибка search_in_main_table: {e}')
            print(f'search_in_main_table.error: {e}')

    @classmethod
    def apply_search_filter(cls, model: Union[Select[Tuple], ModelType], **kwargs):
        """
            переопределяемый метод, стоит условия поиска и пагинации при необходимости
            категория wine имеет подкатегории которые как-бы категории поэтому костыль
        """
        wine = ['red', 'white', 'rose', 'sparkling', 'port']
        if not isinstance(model, Select):   # подсчет количества
            query = cls.get_query(Item).join(Item.drink)
        else:
            query = model.join(Item.drink)
        search_str: str = kwargs.get('search_str')
        category_enum: str = kwargs.get('category_enum')
        country_enum: str = kwargs.get('country_enum')
        if category_enum:
            if category_enum in wine:
                subcategory_cond = create_enum_conditions(Subcategory, category_enum)
                query = (query.join(Drink.subcategory).where(subcategory_cond))
            else:
                category_cond = create_enum_conditions(Category, category_enum)
                query = (query
                         .join(Drink.subcategory)
                         .join(Subcategory.category).where(category_cond))
        if country_enum:
            country_cond = create_enum_conditions(Country, country_enum)
            query = (query.join(Drink.subregion)
                     .join(Subregion.region)
                     .join(Region.country).where(country_cond))
        if search_str:
            search_cond = create_search_conditions2(Drink, search_str)
            query = query.where(search_cond)
        return query

    @classmethod
    async def get_list_view(cls, model: ModelType, session: AsyncSession):
        """Получение списка элементов с плоскими полями для ListView"""
        query = select(Item).options(
            selectinload(Item.drink).options(
                selectinload(Drink.subregion).options(
                    selectinload(Subregion.region).options(
                        selectinload(Region.country)
                    )
                ),
                selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness)
            )
        ).order_by(Item.id.asc())

        result = await session.execute(query)
        items = result.scalars().all()
        # Преобразуем в плоские словари
        flat_items = []
        for item in items:
            flat_item = {
                'id': item.id,
                'vol': item.vol,
                'image_id': item.image_id,
                'title': item.drink.title,  # будет обработано в сервисе для нужного языка
                'drink': item.drink,
                'subcategory': item.drink.subcategory,
                'country': item.drink.subregion.region.country
            }
            flat_items.append(flat_item)

        return flat_items

    @classmethod
    async def get_detail_view(cls, id: int, model: ModelType, session: AsyncSession) -> Dict[str, Any]:
        """Получение детального представления элемента для DetailView"""
        query = select(Item).options(
            selectinload(Item.drink).options(
                selectinload(Drink.subregion).options(
                    selectinload(Subregion.region).options(
                        selectinload(Region.country)
                    )
                ),
                selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness),
                selectinload(Drink.food_associations).joinedload(DrinkFood.food),
                selectinload(Drink.varietal_associations).joinedload(DrinkVarietal.varietal)
            )
        ).where(Item.id == id)

        result = await session.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            return None
        return item


        # Преобразуем в плоский словарь для детального представления
        flat_item = {
            'id': item.id,
            'vol': item.vol,
            'alc': item.drink.alc,
            'age': item.drink.age,
            'image_id': item.image_id,
            'title': item.drink.title,  # будет обработано в сервисе для нужного языка
            'drink': item.drink,
            'description': item.drink.description,
            'country': item.drink.subregion.region.country,
            'subcategory': item.drink.subcategory,
            'sweetness': item.drink.sweetness
        }

        return flat_item

    @classmethod
    async def get_list_view_page(cls, skip: int, limit: int, model: ModelType, session: AsyncSession):
        """Получение списка элементов с плоскими полями для ListView с пагинацией"""
        query = select(Item).options(
            selectinload(Item.drink).options(
                selectinload(Drink.subregion).options(
                    selectinload(Subregion.region).options(
                        selectinload(Region.country)
                    )
                ),
                selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness)
            )
        )

        query = query.order_by(Item.id.asc())
        count_query = select(func.count()).select_from(Item)
        count_result = await session.execute(count_query)
        total = count_result.scalar()

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        items = result.scalars().all()

        # Преобразуем в плоские словари
        flat_items = []
        for item in items:
            flat_item = {
                'id': item.id,
                'vol': item.vol,
                'image_id': item.image_id,
                'title': item.drink.title,  # будет обработано в сервисе для нужного языка
                'drink': item.drink,
                'subcategory': item.drink.subcategory,
                'country': item.drink.subregion.region.country
            }
            flat_items.append(flat_item)

        return flat_items, total

    @classmethod
    async def search_by_drink_title_subtitle(cls, search_str: str,
                                             session: AsyncSession,
                                             skip: int = None,
                                             limit: int = None
                                             ):
        """Поиск элементов по полям title* и subtitle* связанной модели Drink"""
        from app.core.config.project_config import settings
        from app.core.utils.alchemy_utils import build_search_condition, SearchType

        # Получаем список языков из настроек
        langs = settings.LANGUAGES

        # Создаем список полей для поиска
        title_fields = []
        subtitle_fields = []

        for lang in langs:
            if lang == 'en':
                title_fields.append(getattr(Drink, 'title'))
                subtitle_fields.append(getattr(Drink, 'subtitle'))
            else:
                title_fields.append(getattr(Drink, f'title_{lang}', None))
                subtitle_fields.append(getattr(Drink, f'subtitle_{lang}', None))

        # Убираем None значения из списка
        title_fields = [field for field in title_fields if field is not None]
        subtitle_fields = [field for field in subtitle_fields if field is not None]

        # Создаем условия поиска
        search_conditions = []

        for field in title_fields + subtitle_fields:
            condition = build_search_condition(field, search_str, search_type=SearchType.LIKE)
            search_conditions.append(condition)

        # Объединяем все условия с помощью OR
        if search_conditions:
            search_condition = or_(*search_conditions)
        else:
            # Если нет подходящих полей для поиска, возвращаем пустой результат
            return [], 0

        # Формируем запрос с JOIN на Drink
        query = select(Item).options(
            selectinload(Item.drink).options(
                selectinload(Drink.subregion).options(
                    selectinload(Subregion.region).options(
                        selectinload(Region.country)
                    )
                ),
                selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness)
            )
        ).join(Item.drink).where(Drink.id.in_(matching_drink_ids))

        query = query.order_by(Item.id.asc())

        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        result = await session.execute(query)
        items = result.scalars().all()

        # Преобразуем в плоские словари
        flat_items = []
        for item in items:
            flat_item = {
                'id': item.id,
                'vol': item.vol,
                'image_id': item.image_id,
                'title': item.drink.title,  # будет обработано в сервисе для нужного языка
                'drink': item.drink,
                'subcategory': item.drink.subcategory,
                'country': item.drink.subregion.region.country
            }
            flat_items.append(flat_item)

        return flat_items, total

    @classmethod
    async def search_by_trigram_index(cls, search_str: str, model: ModelType, session: AsyncSession,
                                      skip: int = None, limit: int = None):
        """Поиск элементов с использованием триграммного индекса в связанной модели Drink"""
        if search_str is None or search_str.strip() == '':
            # Если search_str пустой, возвращаем все записи с пагинацией
            return await cls.get_list_view_page(skip, limit, model, session)

        # Создаем строку для поиска с использованием триграммного индекса
        # Используем ту же логику, что и в индексе drink_trigram_idx_combined
        search_expr = get_drink_search_expression(Drink)

        # First, get matching drink IDs to avoid loading all related data during search
        drink_search_query = select(Drink.id).where(
            search_expr.cast(String).ilike(f'%{search_str}%')
        )

        if skip is not None:
            drink_search_query = drink_search_query.offset(skip)
        if limit is not None:
            drink_search_query = drink_search_query.limit(limit)

        result = await session.execute(drink_search_query)
        matching_drink_ids = [row[0] for row in result.fetchall()]

        if not matching_drink_ids:
            return [], 0

        # Count total matching records
        count_query = select(func.count(Item.id)).join(Item.drink).where(Drink.id.in_(matching_drink_ids))
        count_result = await session.execute(count_query)
        total = count_result.scalar()

        # Now get the actual items with their related data
        query = select(Item).options(
            selectinload(Item.drink).options(
                selectinload(Drink.subregion).options(
                    selectinload(Subregion.region).options(
                        selectinload(Region.country)
                    )
                ),
                selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness)
            )
        ).join(Item.drink).where(Drink.id.in_(matching_drink_ids))

        query = query.order_by(Item.id.asc())

        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        result = await session.execute(query)
        items = result.scalars().all()

        # Преобразуем в плоские словари
        flat_items = []
        for item in items:
            flat_item = {
                'id': item.id,
                'vol': item.vol,
                'image_id': item.image_id,
                'title': item.drink.title,  # будет обработано в сервисе для нужного языка
                'drink': item.drink,
                'subcategory': item.drink.subcategory,
                'country': item.drink.subregion.region.country
            }
            flat_items.append(flat_item)

        return flat_items, total


def get_drink_search_expression(cls):
    """
        для поиска по триграммному индексу с использованием литералов
    """

    # Определяем литералы для пустой строки и пробела
    EMPTY_STRING = literal_column("''")
    SPACE = literal_column("' '")

    return (func.coalesce(cls.title, EMPTY_STRING) + SPACE + func.coalesce(
        cls.title_ru, EMPTY_STRING
    ) + SPACE + func.coalesce(cls.title_fr, EMPTY_STRING) + SPACE + func.coalesce(
        cls.subtitle, EMPTY_STRING
    ) + SPACE + func.coalesce(
        cls.subtitle_ru, EMPTY_STRING
    ) + SPACE + func.coalesce(cls.subtitle_fr, EMPTY_STRING) + SPACE + func.coalesce(
        cls.description, EMPTY_STRING
    ) + SPACE + func.coalesce(
        cls.description_ru, EMPTY_STRING
    ) + SPACE + func.coalesce(cls.description_fr, EMPTY_STRING) + SPACE + func.coalesce(
        cls.recommendation, EMPTY_STRING
    ) + SPACE + func.coalesce(
        cls.recommendation_ru, EMPTY_STRING
    ) + SPACE + func.coalesce(cls.recommendation_fr, EMPTY_STRING) + SPACE + func.coalesce(
        cls.madeof, EMPTY_STRING
    ) + SPACE + func.coalesce(
        cls.madeof_ru, EMPTY_STRING
    ) + SPACE + func.coalesce(cls.madeof_fr, EMPTY_STRING))
