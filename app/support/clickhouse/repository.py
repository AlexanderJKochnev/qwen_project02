# app.support.clickhouse.repository
import json
from typing import List, Dict, Optional
from loguru import logger


class BeverageRepository:
    """Репозиторий для работы с ClickHouse (v2 - 256d)"""

    def __init__(self, client):
        self.client = client
        self.table = "beverages_rag_v2"

    async def vector_search(
            self, query_embedding: List[float], category: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """
        Семантический поиск по 256-мерным векторам.
        """
        params = {'vec': query_embedding, 'limit': limit}

        where_clause = ""
        if category:
            where_clause = "WHERE category = %(category)s"
            params['category'] = category

        # Используем 1 - cosineDistance для получения Similarity (0..1)
        query = f"""
            SELECT
                name,
                brand,
                category,
                country,
                abv,
                price,
                rating,
                description,
                attributes,
                1 - cosineDistance(embedding, %(vec)s) AS similarity
            FROM {self.table}
            {where_clause}
            ORDER BY similarity DESC
            LIMIT %(limit)s
        """

        try:
            # Асинхронный запрос
            result = await self.client.query(query, parameters=params)

            # Если данных нет
            if not result.result_rows:
                return []

            # ВАЖНО: ClickHouse возвращает данные поколоночно.
            # result.result_rows = [(col1_data), (col2_data), ...]
            # Транспонируем их в список строк (tuple)
            column_names = result.column_names
            rows = list(zip(*result.result_rows))

            # Собираем список словарей
            final_items = []
            for row in rows:
                item = dict(zip(column_names, row))

                # Доп. обработка JSON поля attributes, если оно пришло строкой
                if 'attributes' in item and isinstance(item['attributes'], str):
                    try:
                        item['attributes'] = json.loads(item['attributes'])
                    except Exception:
                        item['attributes'] = {}

                # Округляем similarity для красоты
                if 'similarity' in item:
                    item['similarity'] = round(float(item['similarity']), 4)

                final_items.append(item)

            return final_items

        except Exception as e:
            logger.error(f"Error in BeverageRepository.vector_search: {e}")
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
