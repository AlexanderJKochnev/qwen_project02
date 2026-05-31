# app/support/Item/repository.py
from decimal import Decimal
from typing import List, Optional, Tuple, Union

from loguru import logger  # NOQA: F401
from sqlalchemy import column, Float, func, Integer, select, text, values
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from app.core.exceptions import AppBaseException
from app.core.repositories.array_repository import ArrayRepository
from app.core.repositories.search_repository import SearchRepository
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.core.utils.alchemy_utils import exclude_field_list
from app.support.drink.model import Drink
from app.support.drink.repository import DrinkRepository
from app.support.item.model import Item
from app.support.parcel.model import Site
from app.support.producer.model import Producer
from app.support.region.model import Region
from app.support.subcategory.model import Subcategory
from app.support.subregion.model import Subregion


class ItemRepository(ArrayRepository, SearchRepository, Repository):
    model = Item

    @classmethod
    def get_query(cls, model: ModelType):
        """ создание запроса со связанными полями """
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
    async def get_list_view(cls, model: ModelType, session: AsyncSession, limit: int = 20) -> List[ModelType]:
        """
            Получение списка элементов с плоскими полями для ListView
            почему не подходит core get_list?
        """
        try:
            query = cls.get_query_for_list_view(model).order_by(model.id.asc())
            if limit:
                query = query.limit(limit)
            result = await session.execute(query)
            items = result.scalars().all()
            return items
        except Exception as e:
            raise AppBaseException(message=f'get_list_view.error; {str(e)}', status_code=404)

    @classmethod
    async def get_detail_view(cls, id: int, model: ModelType, session: AsyncSession) -> ModelType:
        """Получение детального представления элемента для DetailView"""
        try:
            query = cls.get_query(model).where(model.id == id)
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
            return items, total
        except Exception as e:
            raise AppBaseException(message=f'get_list_view_page.error; {str(e)}', status_code=404)

    @classmethod
    async def find_items_smart_page(
            cls, session: AsyncSession, query_data=None,
            # Передаем наш query_data вместо hashes
            last_score: Optional[Union[Decimal, str, float]] = None, last_id: Optional[int] = None, limit: int = 20,
            jump_pages: int = 5
    ) -> Tuple[List[dict], List[dict]]:
        """
        Универсальный высокопроизводительный FTS поиск с умной пагинацией:
        1. Извлекает релевантность через ts_rank_cd для Сценариев 2 и 3.
        2. Реализует Keyset пагинацию по контракту Preact (Score + ID).
        3. Возвращает данные текущей страницы + якоря для быстрых прыжков.
        """
        ls_param = Decimal(str(last_score)) if last_score is not None else None
        total_needed = (limit * jump_pages) + 1

        # Режим "просмотра всех" (пустая строка поиска)
        is_full_scan = query_data is None

        if is_full_scan:
            # Упрощенный SQL для пустой строки поиска (оставляем БЕЗ ИЗМЕНЕНИЙ)
            query_sql = text(
                """
                        WITH scored_items AS (
                            SELECT i.id,
                                   1.00000000::numeric as score
                            FROM items i
                        ),
                        filtered_items AS (
                            SELECT * FROM scored_items
                            WHERE (CAST(:ls AS numeric) IS NULL OR (
                                score < CAST(:ls AS numeric) OR
                                (score = CAST(:ls AS numeric) AND id >= CAST(:li AS bigint))
                            ))
                        ),
                        ranked_items AS (
                            SELECT *, row_number() OVER (ORDER BY score DESC, id) as rn
                            FROM filtered_items
                            LIMIT :total_needed
                        )
                        SELECT * FROM ranked_items WHERE rn <= :limit
                        UNION ALL
                        SELECT * FROM ranked_items WHERE rn % :limit = 1 AND rn > 1
                        ORDER BY score DESC, id
                    """
            )
            params = {"limit": limit, "total_needed": total_needed, "ls": ls_param, "li": last_id}

        else:
            # Не пустой запрос. В зависимости от Сценария (1, 2, 3) подставляем логику в CTE
            # Сценарий 1 ранжируем как пустой запрос (score=1.0, сортировка по id)
            # Сценарии 2 и 3 ранжируем по реальному ts_rank_cd

            if query_data.scenario == 1:
                score_select = "1.00000000::numeric as score"
                where_clause = "i.search_vector @@ to_tsquery('simple', :fts_query)"
            elif query_data.scenario == 2:
                score_select = "ROUND(ts_rank_cd(i.search_vector, to_tsquery('simple', :fts_query))::numeric, 8) as score"
                where_clause = "i.search_vector @@ to_tsquery('simple', :fts_query)"
            elif query_data.scenario == 3:
                score_select = "ROUND(ts_rank_cd(i.search_vector, to_tsquery('simple', :fts_query))::numeric, 8) as score"
                # В Сценарии 3 добавляем фильтрацию по LIKE в памяти для последнего недописанного слова
                where_clause = """
                        i.search_vector @@ to_tsquery('simple', :fts_query)
                        AND lower(i.search_content) LIKE :like_term
                    """

            query_sql = text(
                f"""
                        WITH scored_items AS (
                            SELECT i.id,
                                   {score_select}
                            FROM items i
                            WHERE {where_clause}
                        ),
                        filtered_items AS (
                            SELECT * FROM scored_items
                            WHERE (CAST(:ls AS numeric) IS NULL OR (
                                score < CAST(:ls AS numeric) OR
                                (score = CAST(:ls AS numeric) AND id <= CAST(:li AS bigint))
                            ))
                        ),
                        ranked_items AS (
                            SELECT *, row_number() OVER (ORDER BY score DESC, id DESC) as rn
                            FROM filtered_items
                            ORDER BY score DESC, id DESC
                            LIMIT :total_needed
                        )
                        SELECT * FROM ranked_items WHERE rn <= :limit
                        UNION ALL
                        SELECT * FROM ranked_items WHERE rn % :limit = 1 AND rn > 1
                        ORDER BY score DESC, id DESC
                    """
            )

            params = {"fts_query": query_data.fts_query,
                      "like_term": f"%{query_data.like_term.lower()}%" if query_data.like_term else None, "limit": limit,
                      "total_needed": total_needed, "ls": ls_param, "li": last_id}

        # Выполнение SQL
        result = await session.execute(query_sql, params)
        rows = result.mappings().all()
        # Формируем ID для второго этапа и якоря (БЕЗ ИЗМЕНЕНИЙ — контракт сохранен)
        current_page_data = [(r['id'], float(r['score'])) for r in rows if r['rn'] <= limit]
        anchors = [{"page_offset": r['rn'] // limit, "last_score": str(r['score']), "last_id": r['id']} for r in rows if
                   r['rn'] > limit]
        items = await cls.get_full_items(session, current_page_data)
        return items, anchors

    @classmethod
    async def get_full_items(cls, session: AsyncSession, id_score_pairs: list[tuple]):
        if not id_score_pairs:
            return []

        # Создаем временную таблицу в памяти запроса из пар (id, score)
        # Это позволит нам заджойниться на них и сохранить сортировку
        v = values(
            column("id", Integer), column("score", Float),  # или Numeric
            name="target_data"
        ).data(id_score_pairs)

        # Берем ваш базовый запрос со всеми связями
        stmt = cls.get_query(Item)

        # Присоединяем наши ID и Score
        stmt = stmt.join(v, Item.id == v.c.id)

        # Сортируем по score и id из нашей временной таблицы
        stmt = stmt.order_by(v.c.score.desc(), v.c.id.desc())

        res = await session.execute(stmt)
        # Возвращаем уникальные объекты (если есть связи lazy=selectin, это важно)
        return res.unique().scalars().all()
        # return list_dict(res.unique().scalars().all())

    @classmethod
    async def get_list_view_by_ids(cls, ids: list, model: ModelType, session: AsyncSession):
        """
            получение списка элементов с плоскими полями для ListView
            по списку ids
        """
        query = cls.get_query_for_list_view(model).where(model.id.in_(ids)).order_by(model.id.asc())
        result = await session.execute(query)
        items = result.scalars().all()
        return items

    # ------- одноразовые и тестирование ------
    @classmethod
    async def get_item_drink(cls, session: AsyncSession):
        """
            получение items with drink only для переноса картинок из mongo в seaweed
            УДАЛИТЬ после импорта
        """
        # query = select(Item).options(selectinload(Item.drink)).where(Item.image_id != '69be8dcf9d1415cddd3420d8')
        stmt = text("""  SELECT i.id, i.image_id, concat(d.title, ', ', d.subtitle)
                    FROM items AS i
                    JOIN drinks AS d ON i.drink_id = d.id
                    WHERE i.image_id != '69be8dcf9d1415cddd3420d8'
                    AND (i.seaweed_fids IS NULL OR array_length(i.seaweed_fids, 1)
                    IS NULL OR array_length(i.seaweed_fids, 1) = 0)
                    ORDER BY id;
                """)
        result = await session.execute(stmt)
        items_list = result.mappings().all()
        return items_list

    @classmethod
    async def get_item_drink2(cls, session: AsyncSession):
        """
            получение items with drink only для переноса картинок из mongo в seaweed
            УДАЛИТЬ после импорта
        """
        # query = select(Item).options(selectinload(Item.drink)).where(Item.image_id != '69be8dcf9d1415cddd3420d8')
        stmt = text("""  SELECT i.id, i.seaweed_fids[1]
                         FROM items AS i
                         JOIN drinks AS d ON i.drink_id = d.id
                         WHERE array_length(i.seaweed_fids, 1) IS NOT NULL
                         ORDER BY id;
                    """)
        result = await session.execute(stmt)
        items_list = result.mappings().all()
        # id, fid
        return items_list

    @classmethod
    async def get_item_drink3(cls, session: AsyncSession):
        """
            получение items with drink only для переноса картинок из mongo в seaweed
            для записи webp (seaweed_fids[1][2] заполнен
        """
        # query = select(Item).options(selectinload(Item.drink)).where(Item.image_id != '69be8dcf9d1415cddd3420d8')
        stmt = text(
            """
                SELECT i.id, i.image_id, concat(d.title, ', ', d.subtitle)
                FROM items AS i
                JOIN drinks AS d ON i.drink_id = d.id
                WHERE i.image_id != '69be8dcf9d1415cddd3420d8'
                AND array_length(i.seaweed_fids, 1) = 2
                ORDER BY id LIMIT 40;
            """
        )
        result = await session.execute(stmt)
        items_list = result.mappings().all()
        # id, fid
        return items_list
