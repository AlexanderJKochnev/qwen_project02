# app.support.clickhouse.dependencies.py
# app/api/dependencies.py
from fastapi import Request, Depends

from app.support.clickhouse.import_service import ImportService
from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.service import EmbeddingService

# Глобальный синглтон для эмбеддингов (создаётся при старте)
_embedding_service = None


async def get_repository(request: Request) -> BeverageRepository:
    """Dependency для репозитория"""
    client = request.app.state.ch_client
    return BeverageRepository(client)


async def get_embedding_service() -> EmbeddingService:
    """Dependency для сервиса эмбеддингов (синглтон)"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def get_import_service(
    request: Request,
    repo: BeverageRepository = Depends(get_repository),
    embedding: EmbeddingService = Depends(get_embedding_service)
) -> ImportService:
    """Dependency для сервиса импорта"""
    return ImportService(repo, embedding)


# Глобальный синглтон для эмбеддингов
_embedding_service = None
