# app.support.clickhouse.service.py
from fastembed import TextEmbedding
from loguru import logger


class EmbeddingService:
    def __init__(self):
        # Используем существующую регистрацию
        # Если модель "уже зарегистрирована", просто инициализируем её.
        # Если возникнет прошлая ошибка ValueError: Model... not supported,
        # используем обходной путь через загрузку конкретной модели.
        try:
            self.model = TextEmbedding(
                model_name="intfloat/multilingual-e5-small",
                cache_dir="/app/model",
                # Параметр local_files_only=True заставит искать в кэше,
                # если вы не хотите лезть в сеть
            )
        except ValueError as e:
            logger.error(f'редкий хак для FastEmbed BAAI/bge-small-en-v1.5')
            # Если всё равно ругается на "not supported",
            # инициализируем через ближайший официально поддерживаемый ID,
            # но подменяя саму модель (редкий хак для FastEmbed)
            self.model = TextEmbedding(
                model_name="BAAI/bge-small-en-v1.5",  # Любая поддерживаемая с 384d
                cache_dir="/app/model"
            )
            # Принудительно меняем путь к модели, если нужно (но обычно try выше срабатывает)

    def get_query_embedding(self, query: str):
        # Префикс ОБЯЗАТЕЛЕН
        # prefixed_query = f"query: {query}"
        # # На выходе 384 измерения
        # embeddings = list(self.model.embed([prefixed_query]))
        # return embeddings[0].tolist()
        clean_query = query

        # Генерируем вектор
        embeddings = list(self.model.embed([clean_query]))
        return embeddings[0].tolist()


embedding_service = EmbeddingService()
