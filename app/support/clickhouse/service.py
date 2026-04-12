# app.support.clickhouse.service.py
import os
from model2vec import StaticModel
from loguru import logger


class EmbeddingService:
    def __init__(self):
        self.model_path = "/app/models"
        self.model_name = "qhoxie/embeddinggemma-model2vec-256d"
        self.model = None

        # 1. Проверяем, есть ли модель локально
        if os.path.exists(os.path.join(self.model_path, "model.safetensors")):
            try:
                logger.info(f"Loading Model2Vec from local path: {self.model_path}")
                os.environ["HF_HUB_OFFLINE"] = "1"
                self.model = StaticModel.from_pretrained(self.model_path)
            except Exception as e:
                logger.error(f"Failed to load local model: {e}")

        # 2. Если локально нет — скачиваем и сохраняем
        if self.model is None:
            try:
                logger.info(f"Downloading model {self.model_name} from HF...")
                os.environ["HF_HUB_OFFLINE"] = "0"
                self.model = StaticModel.from_pretrained(self.model_name)

                # Создаем папку и сохраняем для будущего использования
                os.makedirs(self.model_path, exist_ok=True)
                self.model.save_pretrained(self.model_path)
                logger.success(f"Model saved to {self.model_path} for offline use.")
            except Exception as e:
                logger.error(f"Critical error loading/saving model: {e}")

    def get_query_embedding(self, query: str):
        if not self.model:
            return []
        # Model2Vec очень быстрая, префиксы не нужны
        return self.model.encode(query).tolist()


embedding_service = EmbeddingService()
