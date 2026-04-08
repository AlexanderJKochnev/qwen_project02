# app.support.clickhouse.import_service.py

import asyncio
import pandas as pd
import hashlib
from typing import List, Dict, Callable, Optional
from loguru import logger

from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.schemas import BeverageCreate
from app.support.clickhouse.service import EmbeddingService


class ImportService:
    """Сервис для импорта CSV файлов"""

    def __init__(self, repository: BeverageRepository, embedding_service: EmbeddingService):
        self.repository = repository
        self.embedding_service = embedding_service
        self.batch_size = 500

    async def import_file(
            self, file_path: str, parser_func: Callable, client, on_progress: Optional[Callable] = None
    ) -> Dict:
        """Импорт одного файла"""

        file_name = file_path.split('/')[-1]
        file_hash = self._compute_hash(file_path)

        # Проверка дубликатов
        if await self.repository.file_exists(file_hash):
            logger.info(f"Skipping {file_name} - already imported")
            return {"file": file_name, "status": "skipped", "rows": 0}

        logger.info(f"Importing {file_name}...")

        # Читаем CSV
        df = pd.read_csv(file_path)
        logger.info(f"Read {len(df)} rows")

        # Парсим строки
        parsed_data = []
        texts_for_embedding = []

        for _, row in df.iterrows():
            try:
                data = parser_func(row, file_path)
                parsed_data.append(data)
                texts_for_embedding.append(f"{data['name']}. {data['description']}"[:1000])
            except Exception as e:
                logger.error(f"Parse error: {e}")
                continue

        # Генерируем эмбеддинги (GPU)
        logger.info(f"Generating embeddings for {len(parsed_data)} rows...")
        embeddings = await self.embedding_service.encode_batch(texts_for_embedding, for_import=True)

        # Сохраняем в БД
        inserted = 0
        for i, (data, embedding) in enumerate(zip(parsed_data, embeddings)):
            beverage = BeverageCreate(
                name=data['name'], description=data['description'], category=data['category'],
                country=data.get('country'), brand=data.get('brand'), abv=data.get('abv'),
                price=data.get('price'), rating=data.get('rating'), attributes=data.get('attributes', {})
            )
            await self.repository.create(beverage, file_hash, file_path, embedding)
            inserted += 1

            if on_progress and i % 100 == 0:
                await on_progress(i, len(parsed_data))

        logger.info(f"✅ Imported {inserted} rows from {file_name}")

        return {"file": file_name, "status": "imported", "rows": inserted}

    async def import_multiple(self, files: List[tuple], client, on_file_done: Optional[Callable] = None):
        """Импорт нескольких файлов последовательно (не параллельно, чтобы не перегружать GPU)"""
        results = []
        for file_path, parser in files:
            result = await self.import_file(file_path, parser, client, on_file_done)
            results.append(result)
        return results

    @staticmethod
    def _compute_hash(file_path: str) -> str:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
