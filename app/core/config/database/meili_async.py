# app/core/config/database/meili_async.py

from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.settings import MeilisearchSettings
from app.core.config.project_config import settings
from loguru import logger


class MeiliManager:
    # Изначально клиент не инициализирован
    client: AsyncClient | None = None

    @classmethod
    async def get_client(cls) -> AsyncClient:
        if cls.client is None:
            logger.debug(f"Инициализация Meilisearch по адресу: {settings.MEILISEARCH_URL}")
            cls.client = AsyncClient(
                url=settings.MEILISEARCH_URL,
                api_key=settings.MEILISEARCH_MASTER_KEY
            )
        return cls.client

    @classmethod
    async def disconnect(cls):
        if cls.client is not None:
            # В SDK 2026 года aclose() обязателен для очистки пула
            await cls.client.aclose()
            cls.client = None

# Зависимость для FastAPI


async def get_meili_client():
    # Просто возвращаем уже созданный Singleton клиент
    # Мы НЕ используем здесь yield/async with, так как за закрытие отвечает lifespan
    return await MeiliManager.get_client()
