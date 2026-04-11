# app.support.clickhouse.repository
from typing import Dict, List, Optional


class BeverageRepository:
    """Репозиторий для работы с ClickHouse"""

    def __init__(self, client):
        self.client = client
        self.table = "beverages_rag"

    async def vector_search(self,
                            query_embedding: List[float],
                            category: Optional[str] = None,
                            limit: int = 10) -> List[Dict]:
        """
        Поиск ближайших векторов в ClickHouse по косинусной близости.
        """
        # Преобразуем список float в строку для ClickHouse
        emb_str = ','.join(str(x) for x in query_embedding)

        where_clause = ""
        if category:
            where_clause = f"WHERE category = '{category}'"

        query = f"""
        SELECT
            name, description, category, country, brand, price, rating,
            cosineDistance(embedding, [{emb_str}]) AS distance
        FROM beverages_rag
        {where_clause}
        ORDER BY distance
        LIMIT {limit}
        """

        result = await self.client.query(query)
        rows = result.result_rows
        column_names = result.column_names

        # Преобразуем в список словарей
        items = []
        for row in rows:
            item = dict(zip(column_names, row))
            # Добавляем similarity (1 - distance)
            item['similarity'] = 1 - item['distance']
            items.append(item)

        return items
