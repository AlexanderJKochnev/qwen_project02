# app.support.clickhouse.service.py
from fastembed import TextEmbedding
from fastembed.common.model_description import ModelSource, PoolingType
from loguru import logger


class EmbeddingService:
    def __init__(self):
        # Регистрируем твой локальный ONNX под любым именем
        self.model_name = "fast-e5-local"
        model_path = "/app/onnx"
        try:
            self.model = TextEmbedding(model_name=self.model_name, cache_dir=model_path)
            logger.success(f"Model {self.model_name} loaded from registry")
        except ValueError as e:
            # 2. Если модели НЕТ в реестре, регистрируем её ПРАВИЛЬНО
            logger.info(f"model not found, {e}. Registering custom model {self.model_name}...")
            try:
                TextEmbedding.add_custom_model(
                    model=self.model_name, pooling=PoolingType.MEAN, normalization=True, dim=384,
                    # ВАЖНО: оборачиваем в ModelSource, чтобы не было ошибки 'dict' attribute 'hf'
                    sources=ModelSource(local=model_path), model_file="onnx/model.onnx"
                )
                self.model = TextEmbedding(model_name=self.model_name, cache_dir=model_path)
            except Exception as reg_e:
                # Если всё равно ругается, что зарегистрирована (гонка потоков)
                if "already registered" in str(reg_e):
                    self.model = TextEmbedding(model_name=self.model_name, cache_dir=model_path)
                else:
                    logger.error(f"Failed to register/load: {reg_e}")
                    raise reg_e

    def get_query_embedding(self, query: str):
        # Поскольку в базе НЕТ префиксов, здесь их тоже НЕ ставим
        # Это вернет Similarity ~1.0 для точных совпадений
        embeddings = list(self.model.embed([query]))
        return embeddings[0].tolist()


embedding_service = EmbeddingService()
