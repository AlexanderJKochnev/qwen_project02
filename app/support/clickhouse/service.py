# app.support.clickhouse.service.py
from fastembed import TextEmbedding
from fastembed.common.model_description import PoolingType
from loguru import logger


class EmbeddingService:
    def __init__(self):
        # Регистрируем твой локальный ONNX под любым именем
        self.model_name = "fast-e5-local"
        try:
            TextEmbedding.add_custom_model(
                model=self.model_name,
                pooling=PoolingType.MEAN,
                normalization=True,
                dim=384,
                # Указываем путь к папке, которую создали на Шаге 1
                sources={"local": "./my_e5_onnx_ready"},
                model_file="onnx/model.onnx"
            )
            self.model = TextEmbedding(model_name=self.model_name)
        except Exception as e:
            logger.error(f'TextEmbedding {e}')

    def get_query_embedding(self, query: str):
        # Поскольку в базе НЕТ префиксов, здесь их тоже НЕ ставим
        # Это вернет Similarity ~1.0 для точных совпадений
        embeddings = list(self.model.embed([query]))
        return embeddings[0].tolist()
