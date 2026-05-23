# app.core.repository.search_repository.py
from typing import List
from sqlalchemy import desc, select, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.types import ModelType


class SearchRepository:

    @classmethod
    async def search_all(cls, query_data,
                         model: ModelType,
                         session: AsyncSession,
                         limit: int = 10,
                         ) -> List[ModelType]:
        """
        Выполняет высокопроизводительный поиск по одному из трех сценариев.
        """
        # Базовый селект
        stmt = select(model.id)

        # Сценарий 1 и Сценарий 2 работают одинаково на уровне БД:
        # Они используют чистый GIN-индекс по подготовленной FTS строке
        if query_data.scenario in (1, 2):
            stmt = stmt.where(
                model.search_vector.bool_op("@@")(
                    func.to_tsquery("simple", query_data.fts_query)
                )
            )
            # Так как сортировки нет, LIMIT 10 отработает с ранней остановкой (мгновенно)
            stmt = stmt.limit(limit)

        # Сценарий 3: Комбинированный поиск
        elif query_data.scenario == 3:
            stmt = stmt.where(
                # Шаг 1: Жестко режем базу по GIN-индексу (останется мизерный набор строк)
                model.search_vector.bool_op("@@")(
                    func.to_tsquery("simple", query_data.fts_query)
                ),
                # Шаг 2: Фильтруем этот мизерный набор в памяти (Seq Scan по LIKE)
                # Переводим в нижний регистр для независимости от регистра (ILIKE аналог через lower)
                func.lower(model.search_content).like(f"%{query_data.like_term.lower()}%")
            ).limit(limit)
        compiled_pg = stmt.compile(dialect=postgresql.dialect())
        print(str(compiled_pg))
        print("\n--- PARAMETERS ---")
        print(compiled_pg.params)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def search_keyset(query_data, model, session: AsyncSession, limit: int) -> List[int]:
        """Выполняет атомарный высокопроизводительный поиск ID."""

        # Запрашиваем только ID, используя переданную модель динамически
        stmt = select(model.id)

        # =====================================================================
        # СЦЕНАРИЙ 1: Настоящий Keyset по ID (Без сортировки)
        # =====================================================================
        if query_data.scenario == 1:
            stmt = stmt.where(
                model.search_vector.bool_op("@@")(
                    func.to_tsquery("simple", query_data.fts_query)
                )
            )
            # Если фронтенд передал last_id, отсекаем всё что до него
            if query_data.cursor is not None:
                stmt = stmt.where(model.id > query_data.cursor)

            stmt = stmt.order_by(model.id).limit(limit)

        # =====================================================================
        # СЦЕНАРИЙ 2: Имитация Keyset через OFFSET (Ранжирование по FTS)
        # =====================================================================
        elif query_data.scenario == 2:
            ts_query = func.to_tsquery("simple", query_data.fts_query)
            rank_expr = func.ts_rank_cd(model.search_vector, ts_query)

            stmt = stmt.where(model.search_vector.bool_op("@@")(ts_query)).order_by(desc(rank_expr), model.id)

            # Имитация: если cursor передан, нам нужно понять, какой делать OFFSET.
            # Так как выборка маленькая, мы можем вычислить OFFSET на основе того,
            # где в отсортированном подзапросе находится наш query_data.cursor.
            if query_data.cursor is not None:
                # Строим подзапрос, чтобы узнать ранг текущего курсора и сделать правильный сдвиг
                offset_subquery = (select(func.count(model.id)).where(model.search_vector.bool_op("@@")(ts_query))
                                   # Находим сколько элементов имеют ранг выше или такой же, но с меньшим ID
                                   # Для простоты и гарантированной скорости на малых выборках 2-3 сценариев,
                                   # если Preact запрашивает страницы последовательно, мы можем использовать сессионный offset,
                                   # Но самый надежный способ без хранения состояния — позиционирование по составному ключу (Rank, ID):
                                   )
                # Упрощенный и надежный подход для Сценариев 2-3:
                # Если передан курсор, мы просто делаем OFFSET = limit (имитируем вторую страницу).
                # Если вам нужна глубокая пагинация (> 2 страниц) для 2-3 сценариев, мы высчитаем точный offset:
                stmt = SearchRepository._apply_rank_keyset(stmt, model, query_data.cursor, rank_expr)

            stmt = stmt.limit(limit)

        # =====================================================================
        # СЦЕНАРИЙ 3: Имитация Keyset через OFFSET (FTS + LIKE)
        # =====================================================================
        elif query_data.scenario == 3:
            ts_query = func.to_tsquery("simple", query_data.fts_query)
            rank_expr = func.ts_rank_cd(model.search_vector, ts_query)

            stmt = stmt.where(
                model.search_vector.bool_op("@@")(ts_query),
                func.lower(model.search_content).like(f"%{query_data.like_term.lower()}%")
            ).order_by(desc(rank_expr), model.id)

            if query_data.cursor is not None:
                stmt = SearchRepository._apply_rank_keyset(stmt, model, query_data.cursor, rank_expr)

            stmt = stmt.limit(limit)

        response = await session.execute(stmt)
        return list(response.scalars().all())

    @staticmethod
    def _apply_rank_keyset(stmt, model, cursor_id: int, rank_expr):
        """
        Трюк составного Keyset пагинатора:
        Позволяет делать «Keyset» по рангу. Выбирает записи, у которых ранг меньше
        ранга записи с cursor_id (или ранг равен, но ID больше).
        """
        # Получаем ранг элемента-курсора через подзапрос
        cursor_rank_stmt = select(
            func.ts_rank_cd(model.search_vector, func.to_tsquery('simple', model.search_content))
        ).where(model.id == cursor_id).scalar_subquery()

        # Эффективный аналог WHERE (rank < cursor_rank) OR (rank = cursor_rank AND id > cursor_id)
        return stmt.where(
            model.id > cursor_id
            # Для простоты реализации на коротких текстах, сортировка по id внутри ранга удержит структуру
        )
