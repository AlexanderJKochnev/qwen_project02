# parsers/async_importer_with_gpu.py
import asyncio
import pandas as pd
from typing import List
from app.core.embeddings.hybrid_manager import hybrid_embeddings
from database.clickhouse_client import clickhouse_client
import hashlib
from loguru import logger


class AsyncCSVImporter:
    """Импорт CSV с использованием GPU для эмбеддингов"""

    def __init__(self):
        self.batch_size = 500  # Больше батч для GPU

    async def import_file(self, file_path: str, parser_func, file_name: str):
        """Импорт одного файла с GPU"""

        logger.info(f"Starting import of {file_name}")

        # Читаем CSV
        df = pd.read_csv(file_path)
        logger.info(f"Read {len(df)} rows from {file_name}")

        # Вычисляем хэш файла
        file_hash = self._compute_file_hash(file_path)

        # Проверяем дубликаты
        if await self._is_file_imported(file_hash):
            logger.info(f"Skipping {file_name} - already imported")
            return

        # Подготавливаем данные батчами
        all_data = []
        all_texts = []

        for _, row in df.iterrows():
            try:
                data = parser_func(row, file_path)
                data['file_hash'] = file_hash
                all_data.append(data)
                all_texts.append(f"{data['name']}. {data['description']}"[:1000])
            except Exception as e:
                logger.error(f"Error parsing row: {e}")
                continue

        logger.info(f"Parsed {len(all_data)} valid rows")

        # Генерируем эмбеддинги на GPU (быстро!)
        logger.info("Generating embeddings on GPU...")
        embeddings = await hybrid_embeddings.encode_for_import(
            all_texts, batch_size=self.batch_size
        )

        # Добавляем эмбеддинги к данным
        for data, emb in zip(all_data, embeddings):
            data['embedding'] = emb

        # Вставляем в ClickHouse батчами
        await self._insert_batches(all_data)

        logger.info(f"✅ Imported {len(all_data)} rows from {file_name}")

    async def _insert_batches(self, data: List[Dict], batch_size: int = 1000):
        """Вставка батчами в ClickHouse"""
        client = await clickhouse_client.get_client()

        column_names = ['name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating', 'attributes',
                        'embedding', 'file_hash', 'source_file']

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            rows = [[row.get(col) for col in column_names] for row in batch]

            await client.insert('beverages_rag', rows, column_names=column_names)
            logger.info(f"  Inserted batch {i // batch_size + 1} ({len(batch)} rows)")

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """Вычисление хэша файла"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    @staticmethod
    async def _is_file_imported(file_hash: str) -> bool:
        """Проверка, импортирован ли файл"""
        client = await clickhouse_client.get_client()
        result = await client.query(
            "SELECT COUNT(*) FROM beverages_rag WHERE file_hash = %(hash)s", {'hash': file_hash}
        )
        return result.result_rows[0][0] > 0
