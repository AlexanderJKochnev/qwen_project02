# app.support.clickhouse.dependencies.py
# app/api/dependencies.py
from fastapi import Depends

from app.core.config.database.click_async import get_ch_client
from app.support.clickhouse.import_service import ImportService
from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.service import EmbeddingService


async def get_repository(client=Depends(get_ch_client)) -> BeverageRepository:
    """Dependency для репозитория"""
    return BeverageRepository(client)


async def get_embedding_service() -> EmbeddingService:
    """Dependency для сервиса эмбеддингов (синглтон)"""
    from app.support.clickhouse.service import EmbeddingService
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def get_import_service(
    repo: BeverageRepository = Depends(get_repository),
    embedding: EmbeddingService = Depends(get_embedding_service)
) -> ImportService:
    """Dependency для сервиса импорта"""
    return ImportService(repo, embedding)


# Глобальный синглтон для эмбеддингов
_embedding_service = None
