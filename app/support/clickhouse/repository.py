# app.support.clickhouse.repository
import json
from typing import List, Dict, Optional
from loguru import logger


class BeverageRepository:
    def __init__(self, client):
        self.client = client
        self.table = "beverages_rag"

    async def vector_search(
            self, query_embedding: List[float], category: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        params = {'vec': query_embedding, 'limit': limit}

        where_clause = ""
        if category:
            where_clause = "WHERE category = %(category)s"
            params['category'] = category

        query = f"""
            SELECT
                name, brand, category, country, abv, price, rating, description, attributes,
                cosineDistance(embedding, %(vec)s) AS dist,
                1 - cosineDistance(embedding, %(vec)s) AS similarity
            FROM {self.table}
            {where_clause}
            ORDER BY similarity DESC
            LIMIT %(limit)s
        """

        try:
            # Выполняем запрос
            result = await self.client.query(query, parameters=params)

            if not result.result_rows:
                return []

            # ИСПОЛЬЗУЕМ named_results() — это самый надежный способ для асинхронного клиента.
            # Он возвращает итератор словарей, где ключи — названия колонок.
            final_items = []
            for row_dict in result.named_results():
                # ClickHouse-connect может вернуть JSON как строку или dict
                attrs = row_dict.get('attributes')
                if isinstance(attrs, str):
                    try:
                        row_dict['attributes'] = json.loads(attrs)
                    except Exception:
                        row_dict['attributes'] = {}

                # Округляем для красоты
                if 'similarity' in row_dict:
                    row_dict['similarity'] = round(float(row_dict['similarity']), 4)

                final_items.append(row_dict)

            return final_items

        except Exception as e:
            # logger.exception выведет полное место ошибки
            logger.exception(f"Error in BeverageRepository.vector_search: {e}")
            return []

    async def create(self, data: List[tuple], column_names: List[str]):
        """
        Метод для вставки пачки данных (используется воркером/импортом).
        """
        try:
            await self.client.insert(self.table, data, column_names=column_names)
        except Exception as e:
            logger.error(f"Failed to insert data into {self.table}: {e}")
            raise e
