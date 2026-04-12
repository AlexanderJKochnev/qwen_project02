# app.support.clickhouse.service.py
import os
import json
from model2vec import StaticModel
from loguru import logger


class EmbeddingService:
    def __init__(self):
        self.model_path = "/app/models"
        self.model_name = "qhoxie/embeddinggemma-model2vec-256d"
        self.model = None

        try:
            # 1. Пробуем загрузить локально
            if os.path.exists(os.path.join(self.model_path, "model.safetensors")):
                logger.info(f"Loading Model2Vec from local path: {self.model_path}")
                os.environ["HF_HUB_OFFLINE"] = "1"
                self.model = StaticModel.from_pretrained(self.model_path)
            else:
                # 2. Если нет — качаем
                logger.info(f"Model not found at {self.model_path}. Downloading {self.model_name}...")
                os.environ["HF_HUB_OFFLINE"] = "0"
                self.model = StaticModel.from_pretrained(self.model_name)
                os.makedirs(self.model_path, exist_ok=True)
                self.model.save_pretrained(self.model_path)
                logger.success(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.exception(f"CRITICAL: Failed to initialize EmbeddingService: {e}")

    def get_query_embedding(self, query: str):
        if not self.model:
            logger.error("EmbeddingService: model is None, cannot encode")
            return []
        try:
            return self.model.encode(query).tolist()
        except Exception as e:
            logger.exception(f"EmbeddingService: encode error: {e}")
            return []


embedding_service = EmbeddingService()
