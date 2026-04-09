# app.support.clickhouse.repository.py
from typing import Optional, List, Dict
import json

from app.support.clickhouse.import_service.schemas import BeverageCategory, BeverageCreate


# from app.models.beverage import BeverageCreate, BeverageInDB, BeverageCategory


class BeverageRepository:
    """Репозиторий для работы с ClickHouse"""

    def __init__(self, client):
        self.client = client
        self.table = "beverages_rag"

    async def create(self, data: BeverageCreate, file_hash: str, source_file: str, embedding: List[float]) -> str:
        """Создание записи"""
        result = await self.client.insert(
            self.table, [[data.name, data.description, data.category.value, data.country, data.brand, data.abv,
                          data.price, data.rating, json.dumps(data.attributes), embedding, file_hash, source_file]],
            column_names=['name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating',
                          'attributes', 'embedding', 'file_hash', 'source_file']
        )
        # Получаем последний ID (упрощённо)
        return result

    async def get_by_id(self, beverage_id: str) -> Optional[Dict]:
        """Получение по ID"""
        result = await self.client.query(
            f"SELECT * FROM {self.table} WHERE id = %(id)s", {'id': beverage_id}
        )
        if result.result_rows:
            row = result.result_rows[0]
            return self._row_to_dict(row, result.column_names)
        return None

    async def update(self, beverage_id: str, data: Dict) -> bool:
        """Обновление"""
        set_parts = []
        params = {'id': beverage_id}

        for key, value in data.items():
            if key == 'attributes':
                set_parts.append(f"attributes = %(attributes)s")
                params['attributes'] = json.dumps(value)
            elif key in ['name', 'description', 'category', 'country', 'brand']:
                set_parts.append(f"{key} = %({key})s")
                params[key] = value
            elif key in ['abv', 'price', 'rating']:
                set_parts.append(f"{key} = %({key})s")
                params[key] = value

        if not set_parts:
            return False

        query = f"ALTER TABLE {self.table} UPDATE {', '.join(set_parts)} WHERE id = %(id)s"
        await self.client.query(query, params)
        return True

    async def delete(self, beverage_id: str) -> bool:
        """Удаление"""
        await self.client.query(
            f"ALTER TABLE {self.table} DELETE WHERE id = %(id)s", {'id': beverage_id}
        )
        return True

    async def list_all(
            self, category: Optional[BeverageCategory] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict]:
        """Список с пагинацией"""
        where = f"WHERE category = '{category.value}'" if category else ""
        query = f"""
        SELECT id, name, category, country, brand, price, rating, created_at
        FROM {self.table}
        {where}
        ORDER BY created_at DESC
        LIMIT {limit} OFFSET {offset}
        """
        result = await self.client.query(query)
        return [self._row_to_dict(row, result.column_names) for row in result.result_rows]

    async def vector_search(
            self, query_embedding: List[float], category: Optional[BeverageCategory] = None, limit: int = 10
    ) -> List[Dict]:
        """Векторный поиск"""
        where = f"WHERE category = '{category.value}'" if category else ""
        query = f"""
        SELECT
            name, description, category, country, brand, price, rating,
            cosineDistance(embedding, {query_embedding}) AS distance
        FROM {self.table}
        {where}
        ORDER BY distance
        LIMIT {limit}
        """
        result = await self.client.query(query)
        return [self._row_to_dict(row, result.column_names) for row in result.result_rows]

    async def file_exists(self, file_hash: str) -> bool:
        """Проверка, импортирован ли файл"""
        result = await self.client.query(
            f"SELECT COUNT(*) FROM {self.table} WHERE file_hash = %(hash)s", {'hash': file_hash}
        )
        return result.result_rows[0][0] > 0

    async def ensure_table(self):
        """Создание таблицы если не существует"""
        query = """
        CREATE TABLE IF NOT EXISTS beverages_rag (
            id UUID DEFAULT generateUUIDv4(),
            name String,
            description String,
            category LowCardinality(String),
            country String,
            brand String,
            abv Nullable(Float32),
            price Nullable(Decimal(10,2)),
            rating Nullable(Float32),
            attributes JSON,
            embedding Array(Float32),
            file_hash String,
            source_file String,
            created_at DateTime DEFAULT now(),
            INDEX idx_category (category) TYPE minmax GRANULARITY 1,
            INDEX idx_embedding embedding TYPE vector_similarity('hnsw', 'cosineDistance', 384) GRANULARITY 100
        ) ENGINE = MergeTree
        ORDER BY (category, name, created_at)
        """
        await self.client.query(query)

    def _row_to_dict(self, row, column_names) -> Dict:
        return dict(zip(column_names, row))
