# app.support.clickhouse.repository
from typing import Dict, List, Optional


class BeverageRepository:
    """Репозиторий для работы с ClickHouse"""

    def __init__(self, client):
        self.client = client
        self.table = "beverages_rag_v2"

    async def vector_search(
            self, query_embedding: List[float], category: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """
        Поиск ближайших векторов 384d.
        Использует HNSW индекс за счет ORDER BY distance.
        """

        # Подготавливаем параметры для безопасного запроса
        params = {"query_vec": query_embedding, "limit": limit}

        # Динамически собираем WHERE, если есть категория
        where_clause = ""
        if category:
            where_clause = "WHERE category = %(category)s"
            params["category"] = category

        # ВАЖНО: Используем параметры %(name)s вместо f-строк для данных
        query = f"""
        SELECT
            name,
            description,
            category,
            country,
            brand,
            price,
            rating,
            cosineDistance(embedding, %(query_vec)s) AS distance
        FROM {self.table}
        {where_clause}
        ORDER BY distance ASC
        LIMIT %(limit)s
        """

        # clickhouse-connect асинхронно выполнит запрос и подставит параметры
        result = await self.client.query(query, parameters=params)

        items = []
        for row in result.result_rows:
            item = dict(zip(result.column_names, row))
            # similarity = 1 - distance (для косинусного расстояния)
            item['similarity'] = round(1 - item['distance'], 4)
            items.append(item)

        return items
