# app.support.clickhouse.service.py
# app.support.clickhouse.service.py
from fastembed import TextEmbedding
import os
from loguru import logger


class EmbeddingService:
    def __init__(self):
        # Используем имя из "белого списка" FastEmbed с той же размерностью (384)
        # Это заставит библиотеку пропустить валидацию имени.
        self.fake_model_name = "BAAI/bge-small-en-v1.5"
        model_path = "/app/onnx"

        try:
            # Библиотека думает, что грузит BGE, но возьмет твои файлы E5 из model_path
            self.model = TextEmbedding(
                model_name=self.fake_model_name,
                cache_dir=model_path,
                local_files_only=True,
                threads=None
            )
            logger.success(f"EmbeddingService: E5 weights loaded via alias {self.fake_model_name}")
        except Exception as e:
            self.model = None
            logger.error(f'EmbeddingService.__init__ failed: {e}')

    def get_query_embedding(self, query: str):
        if self.model is None:
            return []
        try:
            # Генерируем вектор. Т.к. веса внутри ONNX от E5, на выходе будет E5-вектор
            embeddings = list(self.model.embed([query]))
            # Возвращаем первый вектор в списке
            return embeddings[0].tolist()
        except Exception as e:
            logger.error(f"EmbeddingService error: {e}")
            return []


embedding_service = EmbeddingService()
