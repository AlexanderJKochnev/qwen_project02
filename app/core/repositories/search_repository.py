# app.core.repository.search_repository.py
from typing import List
from sqlalchemy import select, func
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

        result = await session.execute(stmt)
        return list(result.scalars().all())
