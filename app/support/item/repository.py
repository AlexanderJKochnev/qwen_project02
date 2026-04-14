# app/support/Item/repository.py
import math
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from sqlalchemy import func, literal_column, or_, select, Select, desc, text
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload
from sqlalchemy.types import String
from app.core.exceptions import AppBaseException
from app.core.config.project_config import settings
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.core.utils.alchemy_utils import build_search_condition, create_enum_conditions, create_search_conditions2, \
    exclude_field_list, SearchType
from app.support.category.model import Category
from app.support.country.model import Country
from app.support.drink.model import Drink
from app.support.drink.repository import DrinkRepository  # , get_drink_search_expression
from app.support.hashing.model import WordHash
from app.support.item.model import Item
from app.support.parcel.model import Site
from app.support.producer.model import Producer
from app.support.region.model import Region
from app.support.subcategory.model import Subcategory
from app.support.subregion.model import Subregion


# from app.core.config.database.db_noclass import get_db


# ItemRepository = RepositoryFactory.get_repository(Item)
class ItemRepository(Repository):
    model = Item

    @classmethod
    def get_query(cls, model: ModelType):
        excl = exclude_field_list(Item, ('search_vector', 'drink', 'search_content'))
        subquery = DrinkRepository.get_selectin()
        query = select(Item).options(load_only(*excl), selectinload(Item.drink).options(*subquery))
        return query

    @classmethod
    def get_query_for_list_view(cls, model: ModelType):
        """
            get_query для запроса list_view - без varietals & foods
        """
        query = select(Item).options(
            selectinload(Item.drink).options(
                selectinload(Drink.site).selectinload(Site.subregion).selectinload(
                    Subregion.region
                ).selectinload(
                    Region.country
                ), selectinload(Drink.subcategory).selectinload(Subcategory.category),
                selectinload(Drink.sweetness),
                # selectinload(Drink.food_associations),
                # selectinload(Drink.varietal_associations), selectinload(Drink.source),
                selectinload(Drink.producer).selectinload(Producer.producertitle), selectinload(Drink.parcel),
                selectinload(Drink.designation), selectinload(Drink.classification),
                selectinload(Drink.vintageconfig)
            )
        )
        return query

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
            raise AppBaseException(message=f'search_geans.error; {str(e)}', status_code=404)

    @classmethod
    def apply_search_filter(cls, model: Union[Select[Tuple], ModelType], **kwargs):
        """
            переопределяемый метод, стоит условия поиска и пагинации при необходимости
            категория wine имеет подкатегории которые как-бы категории поэтому костыль
        """
        try:
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
        except Exception as e:
            raise AppBaseException(message=f'search_geans.error; {str(e)}', status_code=404)

    @classmethod
    async def get_list_view(cls, model: ModelType, session: AsyncSession):
        """Получение списка элементов с плоскими полями для ListView"""
        try:
            query = cls.get_query_for_list_view(Item).order_by(Item.id.asc())
            result = await session.execute(query)
            items = result.scalars().all()
            result = []
            for item in items:
                result.append(item.to_dict())
            return result
        except Exception as e:
            raise AppBaseException(message=f'get_list_view.error; {str(e)}', status_code=404)

    @classmethod
    async def get_detail_view(cls, id: int, model: ModelType, session: AsyncSession) -> Dict[str, Any]:
        """Получение детального представления элемента для DetailView"""
        try:
            query = cls.get_query(Item).where(Item.id == id)
            result = await session.execute(query)
            item = result.scalar_one_or_none()
            # from app.core.utils.common_utils import jprint
            # jprint(item.to_dict())
            # print('--------------------------')
            if not item:
                return None
            return item
        except Exception as e:
            raise AppBaseException(message=f'get_detail_view.error; {str(e)}', status_code=404)

    @classmethod
    async def get_list_view_page(cls, skip: int, limit: int, model: ModelType, session: AsyncSession):
        """Получение списка элементов с плоскими полями для ListView с пагинацией"""
        try:
            query = cls.get_query_for_list_view(Item).order_by(Item.id.asc())
            count_query = select(func.count()).select_from(Item)
            count_result = await session.execute(count_query)
            total = count_result.scalar()

            query = query.offset(skip).limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            result = []
            for item in items:
                result.append(item.to_dict())
            return result, total
        except Exception as e:
            raise AppBaseException(message=f'get_list_view_page.error; {str(e)}', status_code=404)

    @classmethod
    async def search_by_drink_title_subtitle(cls, search_str: str,
                                             session: AsyncSession,
                                             skip: int = None,
                                             limit: int = None
                                             ):
        """Поиск элементов по полям title* и subtitle* связанной модели Drink"""
        # from app.core.config.project_config import settings
        # from app.core.utils.alchemy_utils import build_search_condition, SearchType

        # Получаем список языков из настроек
        try:
            langs = settings.LANGUAGES

            # Создаем список полей для поиска
            title_fields = []
            subtitle_fields = []

            for lang in langs:
                if lang == settings.DEFAULT_LANG:
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
            query = cls.get_query(Item).join(Item.drink).where(search_condition)
            query = query.order_by(Item.id.asc())
            # Получаем общее количество записей
            count_query = select(func.count(Item.id)).join(Item.drink).where(search_condition)
            count_result = await session.execute(count_query)
            total = count_result.scalar()

            # Добавляем пагинацию
            if skip is not None:
                query = query.offset(skip)
            if limit is not None:
                query = query.limit(limit)

            result = await session.execute(query)
            items = result.scalars().all()
            result = []
            for item in items:
                result.append(item.to_dict())
            return result, total
        except Exception as e:
            raise AppBaseException(message=f'search_by_drink_title_subtitle.error; {str(e)}', status_code=404)

    @classmethod
    async def search_by_trigram_index(cls, search_str: str, model: ModelType, session: AsyncSession,
                                      skip: int = None, limit: int = None):
        """Поиск элементов с использованием триграммного индекса в связанной модели Drink"""
        try:
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
            # compiled = drink_search_query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            # logger.info(compiled)
            result = await session.execute(drink_search_query)
            matching_drink_ids = [row[0] for row in result.fetchall()]

            if not matching_drink_ids:
                return [], 0

            # Count total matching records
            count_query = select(func.count(Item.id)).join(Item.drink).where(Drink.id.in_(matching_drink_ids))
            count_result = await session.execute(count_query)
            total = count_result.scalar()

            # Now get the actual items with their related data
            query = cls.get_query(Item).join(Item.drink).where(Drink.id.in_(matching_drink_ids))

            query = query.order_by(Item.id.asc())

            if skip is not None:
                query = query.offset(skip)
            if limit is not None:
                query = query.limit(limit)

            result = await session.execute(query)
            items = result.scalars().all()
            result = []
            for item in items:
                result.append(item.to_dict())
            return result, total
        except Exception as e:
            raise AppBaseException(message=f'search_by_trigramm_index.error; {str(e)}', status_code=404)

    @classmethod
    async def search_by_drink_title_subtitle_only(
            cls, search_str: str, session: AsyncSession):
        """Поиск элементов по полям title* и subtitle* связанной модели Drink"""
        try:
            # Получаем список языков из настроек
            langs = settings.LANGUAGES

            # Создаем список полей для поиска
            title_fields = []
            subtitle_fields = []

            for lang in langs:
                if lang == settings.DEFAULT_LANG:
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
            query = cls.get_query(Item).join(Item.drink).where(search_condition)
            query = query.order_by(Item.id.asc())

            result = await session.execute(query)
            items = result.scalars().all()
            return items
        except Exception as e:
            raise AppBaseException(message=f'search_by_drink_title_subtitle_only.error; {str(e)}', status_code=404)

    @staticmethod
    async def find_items_weighted(
            session: AsyncSession, word_stats: list[dict],  # [{'hash': int, 'freq': int}]
            boost: float = 10.0, limit: int = 15
    ):
        """
            поиск по хэш индексу с учетом частотности слов
            word_stats:
            boost: коэффициент редкости - чем выше тем значимее редкое слово в ранжировании
            limit:
        """
        if not word_stats:
            return []

        # Рассчитываем веса на стороне Python: W = boost / log(freq + 1.5)
        # Добавляем 1.5, чтобы избежать деления на ноль и слишком резких скачков
        case_parts = []
        hashes_list = []

        for item in word_stats:
            h, freq = item['hash'], item['freq']
            weight = (1.0 / math.log(freq + 1.5)) * boost
            # CASE проверяет вхождение каждого хеша из запроса в массив word_hashes записи
            case_parts.append(f"CASE WHEN word_hashes @> ARRAY[{h}::bigint] THEN {weight:.4f} ELSE 0 END")
            hashes_list.append(h)

        score_sql = f"({' + '.join(case_parts)})"

        stmt = (select(Item, text(f"{score_sql} AS score")).where(Item.word_hashes.overlap(hashes_list)).order_by(
            desc(text("score"))
        ).limit(limit))

        result = await session.execute(stmt)
        # return result.all()
        return [{'id': item.id, 'score': score} for item, score in result]

    @staticmethod
    async def get_hashes_by_prefix(session: AsyncSession, prefix: str, limit: int = 50) -> List[WordHash]:
        """
        Поиск хешей в словаре по префиксу последнего слова.
        """
        stmt = (select(WordHash.hash).where(WordHash.word.like(f"{prefix.lower()}%")).order_by(
            WordHash.freq.desc()
        ).limit(limit))
        res = await session.execute(stmt)
        return res.scalars().all()


def get_drink_search_expression(cls):
    """
        для поиска по триграммному индексу с использованием литералов
    """
    try:
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
    except Exception as e:
        raise AppBaseException(message=f'get_drink_search_expression.error; {str(e)}', status_code=404)
