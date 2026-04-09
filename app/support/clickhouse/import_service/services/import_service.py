# app.support.clickhouse.import_service.services.import_service.py
import hashlib

import pandas as pd
from loguru import logger
from app.support.clickhouse.import_service.schemas import BeverageCreate
from app.support.clickhouse.import_service.services.embedding import ImportEmbedding


class ImportService:
    def __init__(self, repo, data_dir, cache_dir):
        self.repo = repo
        self.data_dir = data_dir
        self.embedder = ImportEmbedding(cache_dir)

    async def import_file(self, file_name: str, parser_func):
        file_path = self.data_dir / file_name
        file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
        if await self.repo.file_exists(file_hash):
            logger.info(f"Skipping {file_name} (already imported)")
            return
        df = pd.read_csv(file_path)
        parsed = []
        texts = []
        for _, row in df.iterrows():
            data = parser_func(row, str(file_path))
            parsed.append(data)
            texts.append(f"{data['name']}. {data['description']}"[:1000])
        embeddings = self.embedder.encode(texts)
        for data, emb in zip(parsed, embeddings):
            bev = BeverageCreate(...)
            await self.repo.create(bev, file_hash, str(file_path), emb)
        self.embedder.unload()
