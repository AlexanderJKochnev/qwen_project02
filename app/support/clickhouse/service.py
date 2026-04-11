# app.support.clickhouse.service.py
import os
from typing import List
from fastembed import TextEmbedding


class EmbeddingService:
    def __init__(self):
        # Если ваш HF кэш находится в нестандартном месте, раскомментируйте:
        os.environ["HF_HOME"] = "/app/cache"

        # FastEmbed возьмет multilingual-e5-small, которая дает 384d.
        # При первом запуске он создаст оптимизированную копию в cache_dir.
        self.model = TextEmbedding(
            model_name="intfloat/multilingual-e5-small", cache_dir="./.fastembed_cache"
        )

    def get_query_embedding(self, query: str) -> List[float]:
        """
        Преобразует текст в вектор 384d на CPU.
        """
        # Префикс 'query: ' обязателен для моделей E5!
        prefixed_query = f"query: {query}"

        # Инференс через ONNX (очень быстро на CPU)
        # embed() возвращает итератор, берем первый (и единственный) элемент
        embeddings = list(self.model.embed([prefixed_query]))
        return embeddings[0].tolist()


# Инициализируем один раз при импорте
embedding_service = EmbeddingService()
