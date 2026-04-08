# app.support.clickhouse.import_service.py

import asyncio
import pandas as pd
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from loguru import logger

from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.schemas import BeverageCategory, BeverageCreate
from app.support.clickhouse.service import EmbeddingService


class ImportService:
    def __init__(self, repository: BeverageRepository, embedding_service: EmbeddingService):
        self.repository = repository
        self.embedding_service = embedding_service
        self.data_dir = Path("/app/data")   # CSV файлы монтируются сюда
        self.batch_size = 500

    async def import_file(self, file_name: str, parser_func: Callable,
                          on_progress: Optional[Callable] = None) -> Dict[str, Any]:
        """Импорт одного CSV файла из /app/data/"""
        file_path = self.data_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"CSV not found: {file_path}")

        file_hash = self._compute_hash(file_path)

        # Проверка дубликатов
        if await self.repository.file_exists(file_hash):
            logger.info(f"Skipping {file_name} - already imported")
            return {"file": file_name, "status": "skipped", "rows": 0}

        logger.info(f"Importing {file_name}...")

        # Читаем CSV
        df = pd.read_csv(file_path)
        total_rows = len(df)
        logger.info(f"Read {total_rows} rows")

        # Парсим строки
        parsed_data = []
        texts_for_embedding = []
        for _, row in df.iterrows():
            try:
                data = parser_func(row, str(file_path))
                parsed_data.append(data)
                texts_for_embedding.append(f"{data['name']}. {data['description']}"[:1000])
            except Exception as e:
                logger.error(f"Parse error in {file_name}: {e}")
                continue

        if not parsed_data:
            logger.warning(f"No valid rows in {file_name}")
            return {"file": file_name, "status": "failed", "rows": 0}

        # Генерируем эмбеддинги (полная модель, GPU/CPU)
        logger.info(f"Generating embeddings for {len(parsed_data)} rows...")
        embeddings = await self.embedding_service.encode_batch(texts_for_embedding, for_import=True)

        # Сохраняем в БД
        inserted = 0
        for i, (data, emb) in enumerate(zip(parsed_data, embeddings)):
            # Преобразуем категорию из строки в enum (если нужно)
            try:
                category = BeverageCategory(data['category'])
            except ValueError:
                category = BeverageCategory.OTHER  # fallback

            beverage = BeverageCreate(
                name=data['name'],
                description=data['description'],
                category=category,
                country=data.get('country'),
                brand=data.get('brand'),
                abv=data.get('abv'),
                price=data.get('price'),
                rating=data.get('rating'),
                attributes=data.get('attributes', {})
            )
            await self.repository.create(beverage, file_hash, str(file_path), emb)
            inserted += 1
            if on_progress and i % 100 == 0:
                await on_progress(i, len(parsed_data))

        # ✅ ПРИНУДИТЕЛЬНАЯ ВЫГРУЗКА GPU-МОДЕЛИ ПОСЛЕ ИМПОРТА
        self.embedding_service.unload_import_model()

        logger.info(f"✅ Imported {inserted} rows from {file_name}. GPU model unloaded.")
        return {"file": file_name, "status": "imported", "rows": inserted}

    async def import_multiple(self, files: List[tuple], on_file_done: Optional[Callable] = None) -> List[Dict]:
        """Импорт нескольких файлов. GPU-модель выгружается после КАЖДОГО файла,
        чтобы не занимать VRAM между файлами (если между ними большие паузы)."""
        results = []
        for file_name, parser in files:
            result = await self.import_file(file_name, parser, on_file_done)
            results.append(result)
        return results

    @staticmethod
    def _compute_hash(file_path: Path) -> str:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
