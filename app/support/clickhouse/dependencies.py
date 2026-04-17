# app.support.clickhouse.dependencies.py
# app/api/dependencies.py
from fastapi import Request

# from app.support.clickhouse.import_service.beverage_repository import BeverageRepository
from app.support.clickhouse.service import EmbeddingService
from app.support.clickhouse.repository import BeverageRepository

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
        pass
        # _embedding_service = EmbeddingService()
    return _embedding_service
