# app.support.clickhouse.service.py
from model2vec import StaticModel
from loguru import logger


class EmbeddingService:
    def __init__(self):
        try:
            # Загружаем компактную статическую модель (256d)
            self.model = StaticModel.from_pretrained("qhoxie/embeddinggemma-model2vec-256d")
            logger.success("EmbeddingService: Static Model 256d loaded (CPU Optimized)")
        except Exception as e:
            logger.error(f"Failed to load static model: {e}")
            self.model = None

    def get_query_embedding(self, query: str):
        if not self.model:
            return []
        # Просто текст, никакой структуры!
        vector = self.model.encode(query)
        return vector.tolist()


embedding_service = EmbeddingService()
