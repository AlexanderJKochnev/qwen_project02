# app.support.clickhouse.service.py
from fastembed import TextEmbedding
import os
from loguru import logger


class EmbeddingService:
    def __init__(self):
        # Используем стандартное имя, но локальные файлы
        self.model_name = "intfloat/multilingual-e5-small"

        # Путь ВНУТРИ контейнера (согласно твоему маппингу)
        model_path = "/app/onnx"

        # Инициализируем без add_custom_model, используя встроенный механизм
        try:
            self.model = TextEmbedding(
                model_name=self.model_name, cache_dir=model_path, local_files_only=True, threads=os.cpu_count()
            )
        except Exception as e:
            logger.error(f'EmbeddingService.__init__ {e}')

    def get_query_embedding(self, query: str):
        # embed возвращает итератор, берем первый элемент (вектор 384d)
        embeddings = list(self.model.embed([query]))
        # Важно: embeddings[0] это numpy array, .tolist() делает его Array(Float32) для CH
        return embeddings[0].tolist()


embedding_service = EmbeddingService()
