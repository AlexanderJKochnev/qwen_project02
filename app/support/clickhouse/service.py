# app.support.clickhouse.service.py
from fastembed import TextEmbedding
from fastembed.common.model_description import PoolingType, ModelSource


class EmbeddingService:
    def __init__(self):
        # 1. Регистрируем модель вручную
        # FastEmbed сам скачает ONNX-веса с HF, если их нет в cache_dir
        TextEmbedding.add_custom_model(
            model="intfloat/multilingual-e5-small", pooling=PoolingType.MEAN, normalization=True, dim=384,
            sources=ModelSource(hf="intfloat/multilingual-e5-small"), model_file="onnx/model.onnx"
        )

        # 2. Теперь модель доступна для инициализации
        self.model = TextEmbedding(
            model_name="intfloat/multilingual-e5-small", cache_dir="./.fastembed_cache"
        )

    def get_query_embedding(self, query: str):
        # Обязательный префикс для E5
        prefixed_query = f"query: {query}"
        # Получаем вектор 384d
        embeddings = list(self.model.embed([prefixed_query]))
        return embeddings[0].tolist()


embedding_service = EmbeddingService()
